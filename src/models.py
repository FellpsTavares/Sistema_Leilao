import re
from datetime import date
from src.exceptions import ParticipanteInvalido, LanceInvalido, LeilaoInvalido

class Participante:
    """Representa um participante do leilão."""

    def __init__(self, nome: str, cpf: str, email: str, data_nascimento: date):
        """Inicializa um participante.

        Args:
            nome: Nome completo do participante.
            cpf: CPF do participante (deve ser único).
            email: Email do participante (deve ser único).
            data_nascimento: Data de nascimento do participante.

        Raises:
            ValueError: Se algum dos dados for inválido.
        """
        if not nome or not isinstance(nome, str):
            raise ValueError("Nome inválido.")
        if not self._validar_cpf(cpf):
            raise ValueError("CPF inválido.")
        if not self._validar_email(email):
            raise ValueError("Email inválido.")
        if not isinstance(data_nascimento, date):
            raise ValueError("Data de nascimento inválida.")

        self.nome = nome
        self.cpf = self._formatar_cpf(cpf)
        self.email = email
        self.data_nascimento = data_nascimento
        self._possui_lances = False # Controle interno para regra de exclusão

    def _validar_cpf(self, cpf: str) -> bool:
        """Valida o formato básico do CPF (11 dígitos)."""
        if not cpf or not isinstance(cpf, str):
            return False
        cpf_numerico = re.sub(r'[^0-9]', '', cpf)
        return len(cpf_numerico) == 11

    def _formatar_cpf(self, cpf: str) -> str:
        """Retorna o CPF contendo apenas números."""
        return re.sub(r'[^0-9]', '', cpf)

    def _validar_email(self, email: str) -> bool:
        """Valida o formato básico do email."""
        if not email or not isinstance(email, str):
            return False
        # Regex simples para validação de formato
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return re.match(pattern, email) is not None

    def marcar_como_ofertante(self):
        """Marca que este participante já fez pelo menos um lance."""
        self._possui_lances = True

    @property
    def pode_ser_excluido(self) -> bool:
        """Verifica se o participante pode ser excluído (não possui lances)."""
        return not self._possui_lances

    def __eq__(self, other):
        if not isinstance(other, Participante):
            return NotImplemented
        return self.cpf == other.cpf or self.email == other.email

    def __hash__(self):
        # Usar CPF como hash principal, pois é o identificador único primário
        return hash(self.cpf)

    def __str__(self):
        return f"Participante(Nome: {self.nome}, CPF: {self.cpf}, Email: {self.email})"

    def __repr__(self):
        return f"Participante(nome='{self.nome}', cpf='{self.cpf}', email='{self.email}', data_nascimento={self.data_nascimento!r})"

# --- Classe Lance --- (Conteúdo Omitido para Brevidade)

class Lance:
    """Representa um lance em um leilão."""

    def __init__(self, participante: Participante, valor: float):
        """Inicializa um lance.

        Args:
            participante: O participante que fez o lance.
            valor: O valor do lance.

        Raises:
            ValueError: Se o valor do lance for inválido.
        """
        if not isinstance(participante, Participante):
            raise TypeError("Participante inválido para o lance.")
        if not isinstance(valor, (int, float)) or valor <= 0:
            raise ValueError("O valor do lance deve ser positivo.")

        self.participante = participante
        self.valor = float(valor)

    def __eq__(self, other):
        if not isinstance(other, Lance):
            return NotImplemented
        # Considera lances iguais se participante e valor forem os mesmos
        # Embora na prática isso não deva ocorrer em sequência no mesmo leilão
        return self.participante == other.participante and self.valor == other.valor

    def __lt__(self, other):
        if not isinstance(other, Lance):
            return NotImplemented
        return self.valor < other.valor

    def __le__(self, other):
        if not isinstance(other, Lance):
            return NotImplemented
        return self.valor <= other.valor

    def __gt__(self, other):
        if not isinstance(other, Lance):
            return NotImplemented
        return self.valor > other.valor

    def __ge__(self, other):
        if not isinstance(other, Lance):
            return NotImplemented
        return self.valor >= other.valor

    def __str__(self):
        return f"Lance(Participante: {self.participante.nome}, Valor: R$ {self.valor:.2f})"

    def __repr__(self):
        return f"Lance(participante={self.participante!r}, valor={self.valor})"

# --- Classe Leilao --- (Conteúdo Omitido para Brevidade)
from datetime import datetime, date, time
from enum import Enum, auto

from .exceptions import LanceInvalido, LeilaoInvalido

class EstadoLeilao(Enum):
    INATIVO = auto()
    ABERTO = auto()
    FINALIZADO = auto()
    EXPIRADO = auto()

class Leilao:
    """Representa um leilão de um item."""

    def __init__(self, nome: str, lance_minimo: float, data_inicio: datetime, data_termino: datetime):
        """Inicializa um leilão.

        Args:
            nome: Nome ou descrição do item leiloado.
            lance_minimo: Valor mínimo aceito para um lance.
            data_inicio: Data e hora de início do leilão.
            data_termino: Data e hora de término do leilão.

        Raises:
            ValueError: Se os dados forem inválidos (datas, lance mínimo).
        """
        if not nome or not isinstance(nome, str):
            raise ValueError("Nome do leilão inválido.")
        if not isinstance(lance_minimo, (int, float)) or lance_minimo <= 0:
            raise ValueError("Lance mínimo deve ser positivo.")
        if not isinstance(data_inicio, datetime) or not isinstance(data_termino, datetime):
            raise ValueError("Datas de início e término devem ser objetos datetime.")
        if data_inicio >= data_termino:
            raise ValueError("Data de início deve ser anterior à data de término.")

        self.nome = nome
        self.lance_minimo = float(lance_minimo)
        self.data_inicio = data_inicio
        self.data_termino = data_termino
        self._lances: list[Lance] = []
        self._estado = EstadoLeilao.INATIVO
        self._ganhador: Participante | None = None

        self.atualizar_estado() # Define o estado inicial com base na data atual

    @property
    def estado(self) -> EstadoLeilao:
        """Retorna o estado atual do leilão, atualizando-o se necessário."""
        self.atualizar_estado()
        return self._estado

    @property
    def lances(self) -> list[Lance]:
        """Retorna uma cópia da lista de lances ordenados por valor."""
        return sorted(self._lances, key=lambda lance: lance.valor)

    @property
    def ultimo_lance(self) -> Lance | None:
        """Retorna o último lance válido recebido."""
        return self._lances[-1] if self._lances else None

    @property
    def maior_lance(self) -> Lance | None:
        """Retorna o maior lance do leilão."""
        if not self._lances:
            return None
        return max(self._lances, key=lambda lance: lance.valor)

    @property
    def menor_lance(self) -> Lance | None:
        """Retorna o menor lance do leilão."""
        if not self._lances:
            return None
        return min(self._lances, key=lambda lance: lance.valor)

    @property
    def ganhador(self) -> Participante | None:
        """Retorna o participante ganhador (se o leilão estiver finalizado)."""
        if self.estado == EstadoLeilao.FINALIZADO:
            return self._ganhador
        return None

    def _pode_receber_lance(self, participante: Participante, valor: float) -> bool:
        """Verifica se um lance é válido para este leilão."""
        if self.estado != EstadoLeilao.ABERTO:
            return False # Só aceita lances se estiver ABERTO
        if valor < self.lance_minimo:
            return False # Lance abaixo do mínimo
        if not self._lances:
            return True # Primeiro lance, sempre válido se > mínimo

        ultimo = self.ultimo_lance
        if valor <= ultimo.valor:
            return False # Lance deve ser maior que o último
        if participante == ultimo.participante:
            return False # Mesmo participante não pode dar lances seguidos

        return True

    def propor_lance(self, lance: Lance):
        """Adiciona um lance ao leilão, se válido.

        Args:
            lance: O objeto Lance a ser proposto.

        Raises:
            LanceInvalido: Se o lance não for válido pelas regras do leilão.
            LeilaoInvalido: Se o leilão não estiver no estado ABERTO.
        """
        self.atualizar_estado() # Garante que o estado está atualizado
        if self.estado != EstadoLeilao.ABERTO:
            raise LeilaoInvalido(f"Leilão '{self.nome}' não está ABERTO para receber lances (Estado: {self.estado.name}).")

        if not isinstance(lance, Lance):
            raise TypeError("Objeto de lance inválido.")
        if not self._pode_receber_lance(lance.participante, lance.valor):
            # Determine the reason for invalidity
            motivo = "desconhecido" # Default reason (should ideally be covered by specific checks)
            if lance.valor < self.lance_minimo:
                motivo = f"valor (R$ {lance.valor:.2f}) abaixo do mínimo (R$ {self.lance_minimo:.2f})"
            elif self._lances:
                ultimo = self.ultimo_lance
                if lance.valor <= ultimo.valor:
                    motivo = f"valor (R$ {lance.valor:.2f}) não é maior que o último lance (R$ {ultimo.valor:.2f})"
                elif lance.participante == ultimo.participante:
                    motivo = "participante não pode dar dois lances seguidos"
            raise LanceInvalido(f"Lance inválido para o leilão \'{self.nome}\'. Motivo: {motivo}.")
        self._lances.append(lance)
        lance.participante.marcar_como_ofertante() # Marca que o participante fez um lance

    def atualizar_estado(self):
        """Atualiza o estado do leilão com base nas datas e lances."""
        agora = datetime.now()

        # Apenas FINALIZADO é um estado que nunca deve mudar.
        # EXPIRADO pode, teoricamente, ser recalculado (útil para testes).
        if self._estado == EstadoLeilao.FINALIZADO:
            return # Estados finais não mudam

        if agora < self.data_inicio:
            self._estado = EstadoLeilao.INATIVO
        elif self.data_inicio <= agora < self.data_termino:
            # Se estava INATIVO e a data de início chegou, abre.
            # Ou se estava EXPIRADO e o tempo "voltou" (teste), abre.
            self._estado = EstadoLeilao.ABERTO
        elif agora >= self.data_termino:
            if self._lances:
                self._estado = EstadoLeilao.FINALIZADO
                # Define o ganhador ao finalizar
                maior = self.maior_lance
                if maior:
                    self._ganhador = maior.participante
            else:
                # Se não tem lances e terminou, vai para EXPIRADO.
                self._estado = EstadoLeilao.EXPIRADO

        # ATENÇÃO: Esta é uma simplificação.
        # Se um leilão ABERTO passar da data de término, ele precisa ir para
        # FINALIZADO ou EXPIRADO. A lógica acima cobre isso.
        # Se um leilão INATIVO passar da data de início, ele abre.
        # Se um leilão EXPIRADO for "revisitado" em um tempo ABERTO (teste),
        # ele abrirá.
        # Se um leilão EXPIRADO for "revisitado" em um tempo INATIVO (teste),
        # ele ficará INATIVO.

        # >>>>>> Código Original Modificado <<<<<<
        # A lógica original era:
        # if self._estado == EstadoLeilao.FINALIZADO or self._estado == EstadoLeilao.EXPIRADO:
        #     return
        # A nova lógica permite que EXPIRADO seja recalculado.
        # Também ajustei o bloco ABERTO para ser mais direto.

    @property
    def pode_ser_alterado_ou_excluido(self) -> bool:
        """Verifica se o leilão pode ser alterado ou excluído (apenas INATIVO ou EXPIRADO)."""
        estado_atual = self.estado # Atualiza e obtém o estado
        return estado_atual == EstadoLeilao.INATIVO or estado_atual == EstadoLeilao.EXPIRADO

    def __str__(self):
        return f"Leilão(Nome: {self.nome}, Estado: {self.estado.name}, Lances: {len(self._lances)})"

    def __repr__(self):
        return (f"Leilao(nome='{self.nome}', lance_minimo={self.lance_minimo}, "
                f"data_inicio={self.data_inicio!r}, data_termino={self.data_termino!r})")

