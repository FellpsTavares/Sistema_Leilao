from datetime import datetime, date, time
from typing import List, Optional
import re # Importar re para usar na formatação do CPF

from src.models import Participante, Leilao, EstadoLeilao, Lance
from src.exceptions import ParticipanteInvalido, LeilaoInvalido, LanceInvalido

class SistemaLeiloes:
    """Gerencia o cadastro e operações de participantes e leilões."""

    def __init__(self):
        self._participantes: dict[str, Participante] = {} # CPF -> Participante
        self._leiloes: list[Leilao] = []

    # --- Gerenciamento de Participantes ---

    def cadastrar_participante(self, nome: str, cpf: str, email: str, data_nascimento: date) -> Participante:
        """Cadastra um novo participante no sistema."""
        novo_participante = Participante(nome, cpf, email, data_nascimento)
        cpf_fmt = novo_participante.cpf # CPF já formatado pelo construtor de Participante
        if cpf_fmt in self._participantes:
            raise ParticipanteInvalido(f"CPF {cpf_fmt} já cadastrado.")
        for p in self._participantes.values():
            if p.email == novo_participante.email:
                raise ParticipanteInvalido(f"Email {novo_participante.email} já cadastrado.")
        self._participantes[cpf_fmt] = novo_participante
        return novo_participante

    def _formatar_cpf_busca(self, cpf: str) -> str:
        """Helper para remover formatação do CPF para busca."""
        if not cpf or not isinstance(cpf, str):
            return ""
        return re.sub(r'[^0-9]', '', cpf)

    def buscar_participante_por_cpf(self, cpf: str) -> Optional[Participante]:
        """Busca um participante pelo CPF."""
        cpf_numerico = self._formatar_cpf_busca(cpf)
        return self._participantes.get(cpf_numerico)

    def excluir_participante(self, cpf: str):
        """Exclui um participante do sistema, se possível."""
        participante = self.buscar_participante_por_cpf(cpf)
        cpf_fmt = self._formatar_cpf_busca(cpf) # Usa o CPF formatado para a chave do dict
        if not participante:
            raise ParticipanteInvalido(f"Participante com CPF {cpf_fmt} não encontrado.")
        if not participante.pode_ser_excluido:
            raise ParticipanteInvalido(f"Participante {participante.nome} (CPF: {cpf_fmt}) não pode ser excluído pois possui lances registrados.")
        del self._participantes[cpf_fmt]

    @property
    def participantes(self) -> List[Participante]:
        """Retorna uma lista com todos os participantes cadastrados."""
        return list(self._participantes.values())

    # --- Gerenciamento de Leilões ---

    def cadastrar_leilao(self, nome: str, lance_minimo: float, data_inicio: datetime, data_termino: datetime) -> Leilao:
        """Cadastra um novo leilão no sistema."""
        # Validação de nome único (opcional, mas boa prática)
        if self.buscar_leilao_por_nome(nome):
             raise LeilaoInvalido(f"Já existe um leilão com o nome \'{nome}\'.")
        novo_leilao = Leilao(nome, lance_minimo, data_inicio, data_termino)
        self._leiloes.append(novo_leilao)
        return novo_leilao

    def buscar_leilao_por_nome(self, nome: str) -> Optional[Leilao]:
        """Busca um leilão pelo nome."""
        for leilao in self._leiloes:
            if leilao.nome == nome:
                return leilao
        return None

    def alterar_leilao(self, nome_atual: str, novo_nome: Optional[str] = None, novo_lance_minimo: Optional[float] = None, nova_data_inicio: Optional[datetime] = None, nova_data_termino: Optional[datetime] = None):
        """Altera os dados de um leilão, se permitido."""
        leilao = self.buscar_leilao_por_nome(nome_atual)
        if not leilao:
            # Corrigido: String f fechada corretamente
            raise LeilaoInvalido(f"Leilão com nome \'{nome_atual}\' não encontrado.")

        if not leilao.pode_ser_alterado_ou_excluido:
            # Corrigido: String f fechada corretamente
            raise LeilaoInvalido(f"Leilão \'{leilao.nome}\' não pode ser alterado (Estado: {leilao.estado.name}).")

        # Valida se o novo nome já existe (se for diferente do atual)
        if novo_nome is not None and novo_nome != nome_atual and self.buscar_leilao_por_nome(novo_nome):
            raise LeilaoInvalido(f"Já existe um leilão com o nome \'{novo_nome}\'.")

        temp_nome = novo_nome if novo_nome is not None else leilao.nome
        temp_lance_minimo = novo_lance_minimo if novo_lance_minimo is not None else leilao.lance_minimo
        temp_data_inicio = nova_data_inicio if nova_data_inicio is not None else leilao.data_inicio
        temp_data_termino = nova_data_termino if nova_data_termino is not None else leilao.data_termino

        # Revalidações (algumas podem ser redundantes se Leilao.__init__ for robusto)
        if not temp_nome or not isinstance(temp_nome, str):
            raise ValueError("Novo nome do leilão inválido.")
        if not isinstance(temp_lance_minimo, (int, float)) or temp_lance_minimo <= 0:
            raise ValueError("Novo lance mínimo deve ser positivo.")
        if not isinstance(temp_data_inicio, datetime) or not isinstance(temp_data_termino, datetime):
            raise ValueError("Novas datas de início e término devem ser objetos datetime.")
        if temp_data_inicio >= temp_data_termino:
            raise ValueError("Nova data de início deve ser anterior à nova data de término.")

        leilao.nome = temp_nome
        leilao.lance_minimo = float(temp_lance_minimo)
        leilao.data_inicio = temp_data_inicio
        leilao.data_termino = temp_data_termino
        leilao.atualizar_estado()

    def excluir_leilao(self, nome: str):
        """Exclui um leilão do sistema, se permitido."""
        leilao_para_excluir = None
        indice_para_excluir = -1
        for i, leilao in enumerate(self._leiloes):
            if leilao.nome == nome:
                leilao_para_excluir = leilao
                indice_para_excluir = i
                break
        if not leilao_para_excluir:
            # Corrigido: String f fechada corretamente
            raise LeilaoInvalido(f"Leilão com nome \'{nome}\' não encontrado.")
        if not leilao_para_excluir.pode_ser_alterado_ou_excluido:
            # Corrigido: String f fechada corretamente
            raise LeilaoInvalido(f"Leilão \'{leilao_para_excluir.nome}\' não pode ser excluído (Estado: {leilao_para_excluir.estado.name}).")
        del self._leiloes[indice_para_excluir]

    def listar_leiloes(self, estado: Optional[EstadoLeilao] = None, data_inicio_intervalo: Optional[date] = None, data_fim_intervalo: Optional[date] = None) -> List[Leilao]:
        """Lista leilões, com filtros opcionais por estado e intervalo de datas."""
        leiloes_filtrados = []
        for leilao in self._leiloes:
            leilao.atualizar_estado()
            match = True
            if estado is not None and leilao.estado != estado:
                match = False
            if match and (data_inicio_intervalo is not None or data_fim_intervalo is not None):
                filtro_inicio_dt = datetime.combine(data_inicio_intervalo, time.min) if data_inicio_intervalo else datetime.min
                filtro_fim_dt = datetime.combine(data_fim_intervalo, time.max) if data_fim_intervalo else datetime.max
                # Ajuste para garantir que o filtro funcione corretamente se apenas uma data for fornecida
                if data_inicio_intervalo is None:
                    filtro_inicio_dt = datetime.min
                if data_fim_intervalo is None:
                    filtro_fim_dt = datetime.max

                if not (leilao.data_inicio <= filtro_fim_dt and leilao.data_termino >= filtro_inicio_dt):
                    match = False
            if match:
                leiloes_filtrados.append(leilao)
        return leiloes_filtrados

    # --- Operações de Lances ---

    def propor_lance_sistema(self, cpf_participante: str, nome_leilao: str, valor_lance: float):
        """Permite que um participante proponha um lance para um leilão."""
        participante = self.buscar_participante_por_cpf(cpf_participante)
        if not participante:
            raise ParticipanteInvalido(f"Participante com CPF {cpf_participante} não encontrado.")
        leilao = self.buscar_leilao_por_nome(nome_leilao)
        if not leilao:
            # Corrigido: String f fechada corretamente
            raise LeilaoInvalido(f"Leilão com nome \'{nome_leilao}\' não encontrado.")
        novo_lance = Lance(participante, valor_lance)
        leilao.propor_lance(novo_lance) # Deixa a validação de regras para o Leilao

    def listar_lances_leilao(self, nome_leilao: str) -> List[Lance]:
        """Retorna a lista de lances de um leilão específico, ordenada por valor."""
        leilao = self.buscar_leilao_por_nome(nome_leilao)
        if not leilao:
            # Corrigido: String f fechada corretamente
            raise LeilaoInvalido(f"Leilão com nome \'{nome_leilao}\' não encontrado.")
        return leilao.lances

    def obter_maior_lance_leilao(self, nome_leilao: str) -> Optional[Lance]:
        """Retorna o maior lance de um leilão específico."""
        leilao = self.buscar_leilao_por_nome(nome_leilao)
        if not leilao:
            # Corrigido: String f fechada corretamente
            raise LeilaoInvalido(f"Leilão com nome \'{nome_leilao}\' não encontrado.")
        return leilao.maior_lance

    def obter_menor_lance_leilao(self, nome_leilao: str) -> Optional[Lance]:
        """Retorna o menor lance de um leilão específico."""
        leilao = self.buscar_leilao_por_nome(nome_leilao)
        if not leilao:
            # Corrigido: String f fechada corretamente
            raise LeilaoInvalido(f"Leilão com nome \'{nome_leilao}\' não encontrado.")
        return leilao.menor_lance

    def obter_ganhador_leilao(self, nome_leilao: str) -> Optional[Participante]:
        """Retorna o participante ganhador de um leilão finalizado."""
        leilao = self.buscar_leilao_por_nome(nome_leilao)
        if not leilao:
            # Corrigido: String f fechada corretamente
            raise LeilaoInvalido(f"Leilão com nome \'{nome_leilao}\' não encontrado.")
        return leilao.ganhador

    # --- Notificação ---

    def notificar_ganhador(self, nome_leilao: str) -> bool:
        """Simula o envio de um email para o ganhador do leilão."""
        leilao = self.buscar_leilao_por_nome(nome_leilao)
        if not leilao:
             raise LeilaoInvalido(f"Leilão com nome \'{nome_leilao}\' não encontrado para notificação.")

        ganhador = leilao.ganhador # Pega o ganhador do leilão (que já atualiza o estado)

        if ganhador:
            maior_lance = leilao.maior_lance
            if maior_lance: # Deve sempre existir se houver ganhador
                print(f"--- SIMULAÇÃO DE EMAIL ---")
                print(f"Para: {ganhador.email}")
                # Corrigido: String f fechada corretamente
                print(f"Assunto: Parabéns! Você venceu o leilão \'{leilao.nome}\'")
                print(f"Prezado(a) {ganhador.nome},")
                # Corrigido: String f fechada corretamente
                print(f"Parabéns! Você arrematou o item \'{leilao.nome}\' com o lance de R$ {maior_lance.valor:.2f}.")
                print(f"Detalhes do Leilão:")
                print(f" - Nome: {leilao.nome}")
                # Corrigido: String f fechada corretamente
                print(f" - Data de Término: {leilao.data_termino.strftime('%d/%m/%Y %H:%M:%S')}")
                print(f"Em breve entraremos em contato com mais informações.")
                print(f"""Atenciosamente,
Equipe Leilão System""")
                print(f"--------------------------")
                return True
            else:
                 # Situação inesperada: ganhador sem maior lance?
                 print(f"AVISO: Leilão \'{nome_leilao}\' tem ganhador mas não foi possível obter o maior lance.")
                 return False
        elif leilao.estado == EstadoLeilao.FINALIZADO and not ganhador:
             # Corrigido: String f fechada corretamente
             print(f"AVISO: Leilão \'{nome_leilao}\' está FINALIZADO mas não possui ganhador definido.")
             return False
        elif leilao.estado != EstadoLeilao.FINALIZADO:
             # Corrigido: String f fechada corretamente
             print(f"INFO: Leilão \'{nome_leilao}\' ainda não foi finalizado (Estado: {leilao.estado.name}). Nenhuma notificação enviada.")
             return False
        else: # Caso leilão não encontrado (já tratado no início)
             return False

