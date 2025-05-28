import unittest
from datetime import date, datetime, timedelta, time
import sys
import os
from io import StringIO
from unittest.mock import patch, MagicMock, PropertyMock
import re

# Imports absolutos a partir da raiz do projeto
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, os.pardir))
sys.path.insert(0, project_root)

from src.sistema import SistemaLeiloes
from src.models import Participante, Leilao, EstadoLeilao, Lance
from src.exceptions import ParticipanteInvalido, LeilaoInvalido, LanceInvalido
from freezegun import freeze_time

class TestSistemaLeiloes(unittest.TestCase):

    def setUp(self):
        """Configura um ambiente limpo para cada teste."""
        self.sistema = SistemaLeiloes()
        self.tempo_base = datetime(2025, 5, 23, 12, 0, 0)
        self.agora_dt = self.tempo_base
        self.amanha_dt = self.tempo_base + timedelta(days=1)
        self.ontem_dt = self.tempo_base - timedelta(days=1)
        self.depois_amanha_dt = self.tempo_base + timedelta(days=2)
        self.anteontem_dt = self.tempo_base - timedelta(days=2)
        self.hoje = self.tempo_base.date()
        self.amanha = self.hoje + timedelta(days=1)
        self.ontem = self.hoje - timedelta(days=1)
        self.depois_amanha = self.hoje + timedelta(days=2)
        self.anteontem = self.hoje - timedelta(days=2)

        self.p1 = self.sistema.cadastrar_participante("Alice", "11111111111", "alice@test.com", date(1991, 1, 1))
        self.p2 = self.sistema.cadastrar_participante("Bob", "22222222222", "bob@test.com", date(1992, 2, 2))

    # --- Testes de Participantes ---
    def test_cadastrar_participante_sucesso(self):
        p3 = self.sistema.cadastrar_participante("Charlie", "33333333333", "charlie@test.com", date(1993, 3, 3))
        self.assertIn(p3.cpf, self.sistema._participantes)
        self.assertEqual(self.sistema.buscar_participante_por_cpf("333.333.333-33"), p3)
        self.assertEqual(len(self.sistema.participantes), 3)

    def test_cadastrar_participante_cpf_duplicado(self):
        with self.assertRaisesRegex(ParticipanteInvalido, "CPF 11111111111 já cadastrado."):
            self.sistema.cadastrar_participante("Alice Duplicada", "111.111.111-11", "alice.dup@test.com", date(1991, 1, 1))

    def test_cadastrar_participante_email_duplicado(self):
        with self.assertRaisesRegex(ParticipanteInvalido, "Email alice@test.com já cadastrado."):
            self.sistema.cadastrar_participante("Alice Email Dup", "44444444444", "alice@test.com", date(1994, 4, 4))

    def test_buscar_participante_existente(self):
        self.assertEqual(self.sistema.buscar_participante_por_cpf("11111111111"), self.p1)
        self.assertEqual(self.sistema.buscar_participante_por_cpf("111.111.111-11"), self.p1)

    def test_buscar_participante_inexistente(self):
        self.assertIsNone(self.sistema.buscar_participante_por_cpf("99999999999"))

    # Teste para cobrir linha 32 de sistema.py
    def test_buscar_participante_cpf_invalido_tipo(self):
        self.assertIsNone(self.sistema.buscar_participante_por_cpf(None))
        self.assertIsNone(self.sistema.buscar_participante_por_cpf(12345))

    def test_excluir_participante_sucesso(self):
        cpf_p1 = self.p1.cpf
        self.sistema.excluir_participante(cpf_p1)
        self.assertNotIn(cpf_p1, self.sistema._participantes)
        self.assertIsNone(self.sistema.buscar_participante_por_cpf(cpf_p1))
        self.assertEqual(len(self.sistema.participantes), 1)

    def test_excluir_participante_inexistente(self):
        cpf_inexistente = "99999999999"
        with self.assertRaisesRegex(ParticipanteInvalido, f"Participante com CPF {cpf_inexistente} não encontrado."):
            self.sistema.excluir_participante(cpf_inexistente)

    def test_excluir_participante_com_lances(self):
        inicio_leilao = datetime(2025, 5, 22, 12, 0, 0)
        fim_leilao = datetime(2025, 5, 24, 12, 0, 0)
        tempo_lance = datetime(2025, 5, 23, 12, 0, 0)
        leilao = self.sistema.cadastrar_leilao("Leilao Teste", 10, inicio_leilao, fim_leilao)
        with freeze_time(inicio_leilao - timedelta(hours=1)):
            leilao.atualizar_estado()
            self.assertEqual(leilao.estado, EstadoLeilao.INATIVO)
        with freeze_time(tempo_lance):
            leilao.atualizar_estado()
            self.assertEqual(leilao.estado, EstadoLeilao.ABERTO)
            self.sistema.propor_lance_sistema(self.p1.cpf, "Leilao Teste", 20)
        with self.assertRaisesRegex(ParticipanteInvalido, f"Participante {self.p1.nome} .* não pode ser excluído pois possui lances registrados."):
            self.sistema.excluir_participante(self.p1.cpf)
        self.assertIn(self.p1.cpf, self.sistema._participantes)

    def test_listar_participantes(self):
        participantes = self.sistema.participantes
        self.assertEqual(len(participantes), 2)
        self.assertIn(self.p1, participantes)
        self.assertIn(self.p2, participantes)

    # --- Testes de Leilões ---
    def test_cadastrar_leilao_sucesso(self):
        leilao = self.sistema.cadastrar_leilao("Notebook", 1500, self.amanha_dt, self.depois_amanha_dt)
        self.assertIn(leilao, self.sistema._leiloes)
        self.assertEqual(self.sistema.buscar_leilao_por_nome("Notebook"), leilao)

    def test_cadastrar_leilao_nome_duplicado(self):
        self.sistema.cadastrar_leilao("ItemDup", 100, self.amanha_dt, self.depois_amanha_dt)
        with self.assertRaisesRegex(LeilaoInvalido, r"Já existe um leilão com o nome \'ItemDup\'."):
            self.sistema.cadastrar_leilao("ItemDup", 200, self.amanha_dt, self.depois_amanha_dt)

    def test_buscar_leilao_existente(self):
        leilao = self.sistema.cadastrar_leilao("Celular", 800, self.amanha_dt, self.depois_amanha_dt)
        self.assertEqual(self.sistema.buscar_leilao_por_nome("Celular"), leilao)

    def test_buscar_leilao_inexistente(self):
        self.assertIsNone(self.sistema.buscar_leilao_por_nome("Inexistente"))

    @freeze_time("2025-05-23 10:00:00")
    def test_alterar_leilao_inativo_sucesso(self):
        leilao = self.sistema.cadastrar_leilao("Original", 100, datetime(2025, 5, 24, 12, 0, 0), datetime(2025, 5, 25, 12, 0, 0))
        leilao.atualizar_estado()
        self.assertEqual(leilao.estado, EstadoLeilao.INATIVO)
        self.sistema.alterar_leilao("Original", novo_nome="Alterado", novo_lance_minimo=150, nova_data_inicio=datetime(2025, 5, 24, 14, 0, 0))
        leilao_alterado = self.sistema.buscar_leilao_por_nome("Alterado")
        self.assertIsNotNone(leilao_alterado)
        self.assertEqual(leilao_alterado.lance_minimo, 150)
        self.assertEqual(leilao_alterado.data_inicio, datetime(2025, 5, 24, 14, 0, 0))
        self.assertIsNone(self.sistema.buscar_leilao_por_nome("Original"))

    @freeze_time("2025-05-23 10:00:00")
    def test_alterar_leilao_expirado_sucesso(self):
        leilao = self.sistema.cadastrar_leilao("Expirado", 50, datetime(2025, 5, 21, 10, 0, 0), datetime(2025, 5, 22, 10, 0, 0))
        leilao.atualizar_estado()
        self.assertEqual(leilao.estado, EstadoLeilao.EXPIRADO)
        self.sistema.alterar_leilao("Expirado", novo_lance_minimo=60)
        self.assertEqual(leilao.lance_minimo, 60)

    @freeze_time("2025-05-23 10:00:00")
    def test_alterar_leilao_aberto_falha(self):
        leilao = self.sistema.cadastrar_leilao("Aberto", 50, datetime(2025, 5, 22, 10, 0, 0), datetime(2025, 5, 24, 10, 0, 0))
        leilao.atualizar_estado()
        self.assertEqual(leilao.estado, EstadoLeilao.ABERTO)
        with self.assertRaisesRegex(LeilaoInvalido, r"Leilão \'Aberto\' não pode ser alterado \(Estado: ABERTO\)"):
            self.sistema.alterar_leilao("Aberto", novo_lance_minimo=60)

    def test_alterar_leilao_finalizado_falha(self):
        inicio_leilao = datetime(2025, 5, 21, 10, 0, 0)
        fim_leilao = datetime(2025, 5, 22, 10, 0, 0)
        tempo_lance = datetime(2025, 5, 21, 11, 0, 0)
        with freeze_time(inicio_leilao - timedelta(hours=1)):
            leilao = self.sistema.cadastrar_leilao("Finalizado", 50, inicio_leilao, fim_leilao)
            self.assertEqual(leilao.estado, EstadoLeilao.INATIVO, "Deveria ser INATIVO antes do início")
        with freeze_time(tempo_lance):
            leilao = self.sistema.buscar_leilao_por_nome("Finalizado")
            leilao.atualizar_estado()
            self.assertEqual(leilao.estado, EstadoLeilao.ABERTO, "Leilão deveria estar ABERTO para receber lance")
            self.sistema.propor_lance_sistema(self.p1.cpf, "Finalizado", 60)
        with freeze_time(fim_leilao + timedelta(hours=1)):
            leilao = self.sistema.buscar_leilao_por_nome("Finalizado")
            leilao.atualizar_estado()
            self.assertEqual(leilao.estado, EstadoLeilao.FINALIZADO, "Leilão deveria estar FINALIZADO após o término com lance")
            with self.assertRaisesRegex(LeilaoInvalido, r"Leilão \'Finalizado\' não pode ser alterado \(Estado: FINALIZADO\)"):
                self.sistema.alterar_leilao("Finalizado", novo_lance_minimo=70)

    def test_alterar_leilao_inexistente(self):
        with self.assertRaisesRegex(LeilaoInvalido, r"Leilão com nome \'Inexistente\' não encontrado."):
            self.sistema.alterar_leilao("Inexistente", novo_nome="NovoNome")

    def test_alterar_leilao_novo_nome_duplicado(self):
        l1 = self.sistema.cadastrar_leilao("Leilao1", 100, self.amanha_dt, self.depois_amanha_dt)
        l2 = self.sistema.cadastrar_leilao("Leilao2", 200, self.amanha_dt, self.depois_amanha_dt)
        with self.assertRaisesRegex(LeilaoInvalido, r"Já existe um leilão com o nome \'Leilao2\'."):
            self.sistema.alterar_leilao("Leilao1", novo_nome="Leilao2")

    # Testes para cobrir linhas 95 e 99 de sistema.py
    def test_alterar_leilao_dados_invalidos_extras(self):
        leilao = self.sistema.cadastrar_leilao("ParaAlterarInv", 100, self.amanha_dt, self.depois_amanha_dt)
        with self.assertRaisesRegex(ValueError, "Novo nome do leilão inválido."):
            self.sistema.alterar_leilao("ParaAlterarInv", novo_nome="") # Nome vazio
        # O caso novo_nome=None não deve levantar erro, pois significa não alterar
        # with self.assertRaisesRegex(ValueError, "Novo nome do leilão inválido."):
        #     self.sistema.alterar_leilao("ParaAlterarInv", novo_nome=None) # Nome None
        with self.assertRaisesRegex(ValueError, "Novo nome do leilão inválido."):
            self.sistema.alterar_leilao("ParaAlterarInv", novo_nome=123) # Nome não string

        with self.assertRaisesRegex(ValueError, "Novo lance mínimo deve ser positivo."):
            self.sistema.alterar_leilao("ParaAlterarInv", novo_lance_minimo="abc") # Lance não numérico
        with self.assertRaisesRegex(ValueError, "Novo lance mínimo deve ser positivo."):
            self.sistema.alterar_leilao("ParaAlterarInv", novo_lance_minimo=-50) # Lance negativo
        with self.assertRaisesRegex(ValueError, "Novo lance mínimo deve ser positivo."):
            self.sistema.alterar_leilao("ParaAlterarInv", novo_lance_minimo=0) # Lance zero

        with self.assertRaisesRegex(ValueError, "Novas datas de início e término devem ser objetos datetime."):
            self.sistema.alterar_leilao("ParaAlterarInv", nova_data_inicio="data invalida")
        # O caso nova_data_termino=None não deve levantar erro, pois significa não alterar
        # with self.assertRaisesRegex(ValueError, "Novas datas de início e término devem ser objetos datetime."):
        #     self.sistema.alterar_leilao("ParaAlterarInv", nova_data_termino=None)

        with self.assertRaisesRegex(ValueError, "Nova data de início deve ser anterior à nova data de término."):
            self.sistema.alterar_leilao("ParaAlterarInv", nova_data_inicio=self.depois_amanha_dt, nova_data_termino=self.amanha_dt)

    @freeze_time("2025-05-23 10:00:00")
    def test_excluir_leilao_inativo_sucesso(self):
        leilao = self.sistema.cadastrar_leilao("ParaExcluir", 100, self.amanha_dt, self.depois_amanha_dt)
        leilao.atualizar_estado()
        self.assertEqual(leilao.estado, EstadoLeilao.INATIVO)
        self.sistema.excluir_leilao("ParaExcluir")
        self.assertNotIn(leilao, self.sistema._leiloes)
        self.assertIsNone(self.sistema.buscar_leilao_por_nome("ParaExcluir"))

    @freeze_time("2025-05-23 10:00:00")
    def test_excluir_leilao_expirado_sucesso(self):
        leilao = self.sistema.cadastrar_leilao("ExpiradoExcluir", 50, self.anteontem_dt, self.ontem_dt)
        leilao.atualizar_estado()
        self.assertEqual(leilao.estado, EstadoLeilao.EXPIRADO)
        self.sistema.excluir_leilao("ExpiradoExcluir")
        self.assertNotIn(leilao, self.sistema._leiloes)

    @freeze_time("2025-05-23 10:00:00")
    def test_excluir_leilao_aberto_falha(self):
        leilao = self.sistema.cadastrar_leilao("AbertoExcluir", 50, self.ontem_dt, self.amanha_dt)
        leilao.atualizar_estado()
        self.assertEqual(leilao.estado, EstadoLeilao.ABERTO)
        with self.assertRaisesRegex(LeilaoInvalido, r"Leilão \'AbertoExcluir\' não pode ser excluído \(Estado: ABERTO\)"):
            self.sistema.excluir_leilao("AbertoExcluir")
        self.assertIn(leilao, self.sistema._leiloes)

    def test_excluir_leilao_finalizado_falha(self):
        inicio_leilao = self.anteontem_dt
        fim_leilao = self.ontem_dt
        tempo_lance = inicio_leilao + timedelta(hours=1)
        with freeze_time(inicio_leilao - timedelta(hours=1)):
            leilao = self.sistema.cadastrar_leilao("FinalizadoExcluir", 50, inicio_leilao, fim_leilao)
            self.assertEqual(leilao.estado, EstadoLeilao.INATIVO, "Deveria ser INATIVO antes do início")
        with freeze_time(tempo_lance):
            leilao = self.sistema.buscar_leilao_por_nome("FinalizadoExcluir")
            leilao.atualizar_estado()
            self.assertEqual(leilao.estado, EstadoLeilao.ABERTO, "Leilão deveria estar ABERTO para receber lance")
            self.sistema.propor_lance_sistema(self.p1.cpf, "FinalizadoExcluir", 60)
        with freeze_time(fim_leilao + timedelta(hours=1)):
            leilao = self.sistema.buscar_leilao_por_nome("FinalizadoExcluir")
            leilao.atualizar_estado()
            self.assertEqual(leilao.estado, EstadoLeilao.FINALIZADO, "Leilão deveria estar FINALIZADO após o término com lance")
            with self.assertRaisesRegex(LeilaoInvalido, r"Leilão \'FinalizadoExcluir\' não pode ser excluído \(Estado: FINALIZADO\)"):
                self.sistema.excluir_leilao("FinalizadoExcluir")
            self.assertIn(leilao, self.sistema._leiloes)

    def test_excluir_leilao_inexistente(self):
        with self.assertRaisesRegex(LeilaoInvalido, r"Leilão com nome \'Inexistente\' não encontrado."):
            self.sistema.excluir_leilao("Inexistente")

    def test_listar_leiloes_sem_filtro(self):
        agora = datetime(2025, 5, 23, 10, 0, 0)
        amanha = agora + timedelta(days=1)
        depois_amanha = agora + timedelta(days=2)
        ontem = agora - timedelta(days=1)
        anteontem = agora - timedelta(days=2)
        tres_dias_atras = agora - timedelta(days=3)
        l1 = self.sistema.cadastrar_leilao("L1_Inativo", 10, amanha, depois_amanha)
        l2 = self.sistema.cadastrar_leilao("L2_Aberto", 10, ontem, amanha)
        l3 = self.sistema.cadastrar_leilao("L3_Expirado", 10, anteontem, ontem)
        l4_dt_inicio = tres_dias_atras
        l4_dt_fim = anteontem
        with freeze_time(l4_dt_inicio - timedelta(hours=1)):
            l4 = self.sistema.cadastrar_leilao("L4_Finalizado", 10, l4_dt_inicio, l4_dt_fim)
            self.assertEqual(l4.estado, EstadoLeilao.INATIVO, "L4 deveria ser INATIVO antes do início")
        with freeze_time(l4_dt_inicio + timedelta(hours=1)):
             l4 = self.sistema.buscar_leilao_por_nome("L4_Finalizado")
             l4.atualizar_estado()
             self.assertEqual(l4.estado, EstadoLeilao.ABERTO, "L4 deveria estar ABERTO para receber lance")
             self.sistema.propor_lance_sistema(self.p1.cpf, "L4_Finalizado", 15)
        with freeze_time(agora):
            l1_atual = self.sistema.buscar_leilao_por_nome("L1_Inativo")
            l2_atual = self.sistema.buscar_leilao_por_nome("L2_Aberto")
            l3_atual = self.sistema.buscar_leilao_por_nome("L3_Expirado")
            l4_atual = self.sistema.buscar_leilao_por_nome("L4_Finalizado")
            for leilao in [l1_atual, l2_atual, l3_atual, l4_atual]:
                 if leilao: leilao.atualizar_estado()
            lista = self.sistema.listar_leiloes()
            self.assertEqual(len(lista), 4)
            self.assertIn(l1_atual, lista)
            self.assertIn(l2_atual, lista)
            self.assertIn(l3_atual, lista)
            self.assertIn(l4_atual, lista)
            self.assertEqual(l1_atual.estado, EstadoLeilao.INATIVO)
            self.assertEqual(l2_atual.estado, EstadoLeilao.ABERTO)
            self.assertEqual(l3_atual.estado, EstadoLeilao.EXPIRADO)
            self.assertEqual(l4_atual.estado, EstadoLeilao.FINALIZADO, "L4 deveria estar FINALIZADO agora")

    @freeze_time("2025-05-23 10:00:00")
    def test_listar_leiloes_filtro_estado(self):
        l1 = self.sistema.cadastrar_leilao("L1_Inativo", 10, self.amanha_dt, self.depois_amanha_dt)
        l2 = self.sistema.cadastrar_leilao("L2_Aberto", 10, self.ontem_dt, self.amanha_dt)
        l3 = self.sistema.cadastrar_leilao("L3_Expirado", 10, self.anteontem_dt, self.ontem_dt)
        for leilao in self.sistema._leiloes: leilao.atualizar_estado()
        self.assertEqual(self.sistema.listar_leiloes(estado=EstadoLeilao.INATIVO), [l1])
        self.assertEqual(self.sistema.listar_leiloes(estado=EstadoLeilao.ABERTO), [l2])
        self.assertEqual(self.sistema.listar_leiloes(estado=EstadoLeilao.EXPIRADO), [l3])
        self.assertEqual(self.sistema.listar_leiloes(estado=EstadoLeilao.FINALIZADO), [])

    @freeze_time("2025-05-23 12:00:00")
    def test_listar_leiloes_filtro_data(self):
        l1 = self.sistema.cadastrar_leilao("L1", 10, datetime(2025, 5, 24, 12, 0), datetime(2025, 5, 25, 12, 0))
        l2 = self.sistema.cadastrar_leilao("L2", 10, datetime(2025, 5, 22, 12, 0), datetime(2025, 5, 24, 12, 0))
        l3 = self.sistema.cadastrar_leilao("L3", 10, datetime(2025, 5, 21, 12, 0), datetime(2025, 5, 22, 12, 0))
        l4 = self.sistema.cadastrar_leilao("L4", 10, datetime(2025, 5, 20, 12, 0), datetime(2025, 5, 21, 12, 0))
        for leilao in self.sistema._leiloes: leilao.atualizar_estado()
        filtro_inicio = date(2025, 5, 22)
        filtro_fim = date(2025, 5, 24)
        lista = self.sistema.listar_leiloes(data_inicio_intervalo=filtro_inicio, data_fim_intervalo=filtro_fim)
        self.assertCountEqual(lista, [l1, l2, l3])
        self.assertNotIn(l4, lista)
        lista_inicio = self.sistema.listar_leiloes(data_inicio_intervalo=date(2025, 5, 23))
        self.assertCountEqual(lista_inicio, [l1, l2])
        lista_fim = self.sistema.listar_leiloes(data_fim_intervalo=date(2025, 5, 21))
        self.assertCountEqual(lista_fim, [l3, l4])

    @freeze_time("2025-05-23 12:00:00")
    def test_listar_leiloes_filtro_combinado(self):
        l1 = self.sistema.cadastrar_leilao("L1_Inativo", 10, self.amanha_dt, self.depois_amanha_dt)
        l2 = self.sistema.cadastrar_leilao("L2_Aberto", 10, self.ontem_dt, self.amanha_dt)
        l3 = self.sistema.cadastrar_leilao("L3_Aberto_Antigo", 10, self.anteontem_dt, self.amanha_dt)
        for leilao in self.sistema._leiloes: leilao.atualizar_estado()
        lista = self.sistema.listar_leiloes(estado=EstadoLeilao.ABERTO, data_inicio_intervalo=self.hoje)
        self.assertCountEqual(lista, [l2, l3])
        lista2 = self.sistema.listar_leiloes(estado=EstadoLeilao.ABERTO, data_fim_intervalo=self.amanha)
        self.assertCountEqual(lista2, [l2, l3])

    # --- Testes de Lances via Sistema ---
    @freeze_time("2025-05-23 10:00:00")
    def test_propor_lance_sistema_sucesso(self):
        leilao = self.sistema.cadastrar_leilao("LeilaoLance", 50, self.ontem_dt, self.amanha_dt)
        leilao.atualizar_estado()
        self.assertEqual(leilao.estado, EstadoLeilao.ABERTO)
        self.sistema.propor_lance_sistema(self.p1.cpf, "LeilaoLance", 60)
        self.assertEqual(len(leilao.lances), 1)
        self.assertEqual(leilao.ultimo_lance.valor, 60)
        self.assertEqual(leilao.ultimo_lance.participante, self.p1)

    def test_propor_lance_sistema_participante_inexistente(self):
        leilao = self.sistema.cadastrar_leilao("LeilaoLance", 50, self.ontem_dt, self.amanha_dt)
        with self.assertRaisesRegex(ParticipanteInvalido, "Participante com CPF 99999999999 não encontrado."):
            self.sistema.propor_lance_sistema("99999999999", "LeilaoLance", 60)

    def test_propor_lance_sistema_leilao_inexistente(self):
        with self.assertRaisesRegex(LeilaoInvalido, r"Leilão com nome \'Inexistente\' não encontrado."):
            self.sistema.propor_lance_sistema(self.p1.cpf, "Inexistente", 60)

    @freeze_time("2025-05-23 10:00:00")
    def test_propor_lance_sistema_leilao_nao_aberto(self):
        leilao_inativo = self.sistema.cadastrar_leilao("InativoLance", 50, self.amanha_dt, self.depois_amanha_dt)
        leilao_inativo.atualizar_estado()
        self.assertEqual(leilao_inativo.estado, EstadoLeilao.INATIVO)
        with self.assertRaisesRegex(LeilaoInvalido, r"não está ABERTO para receber lances \(Estado: INATIVO\)"):
            self.sistema.propor_lance_sistema(self.p1.cpf, "InativoLance", 60)

    @freeze_time("2025-05-23 10:00:00")
    def test_propor_lance_sistema_lance_invalido(self):
        leilao = self.sistema.cadastrar_leilao("LeilaoLanceInv", 50, self.ontem_dt, self.amanha_dt)
        leilao.atualizar_estado()
        self.assertEqual(leilao.estado, EstadoLeilao.ABERTO)
        self.sistema.propor_lance_sistema(self.p1.cpf, "LeilaoLanceInv", 60)
        with self.assertRaisesRegex(LanceInvalido, r"valor \(R\$ 55.00\) não é maior que o último lance \(R\$ 60.00\)"):
            self.sistema.propor_lance_sistema(self.p2.cpf, "LeilaoLanceInv", 55)
        with self.assertRaisesRegex(LanceInvalido, "participante não pode dar dois lances seguidos"):
            self.sistema.propor_lance_sistema(self.p1.cpf, "LeilaoLanceInv", 70)

    @freeze_time("2025-05-23 10:00:00")
    def test_listar_lances_leilao_sucesso(self):
        leilao = self.sistema.cadastrar_leilao("LeilaoComLances", 50, self.ontem_dt, self.amanha_dt)
        leilao.atualizar_estado()
        self.assertEqual(leilao.estado, EstadoLeilao.ABERTO)
        l1 = Lance(self.p1, 60)
        l2 = Lance(self.p2, 70)
        l3 = Lance(self.p1, 80)
        leilao.propor_lance(l1)
        leilao.propor_lance(l2)
        leilao.propor_lance(l3)
        lances_listados = self.sistema.listar_lances_leilao("LeilaoComLances")
        self.assertEqual(lances_listados, [l1, l2, l3])

    def test_listar_lances_leilao_sem_lances(self):
        leilao = self.sistema.cadastrar_leilao("LeilaoSemLances", 50, self.ontem_dt, self.amanha_dt)
        self.assertEqual(self.sistema.listar_lances_leilao("LeilaoSemLances"), [])

    def test_listar_lances_leilao_inexistente(self):
        with self.assertRaisesRegex(LeilaoInvalido, r"Leilão com nome \'Inexistente\' não encontrado."):
            self.sistema.listar_lances_leilao("Inexistente")

    @freeze_time("2025-05-23 10:00:00")
    def test_obter_maior_menor_lance_sucesso(self):
        leilao = self.sistema.cadastrar_leilao("LeilaoMM", 50, self.ontem_dt, self.amanha_dt)
        leilao.atualizar_estado()
        self.assertEqual(leilao.estado, EstadoLeilao.ABERTO)
        l1 = Lance(self.p1, 60)
        l2 = Lance(self.p2, 75)
        l3 = Lance(self.p1, 70)
        leilao.propor_lance(l1)
        leilao.propor_lance(l2)
        with self.assertRaises(LanceInvalido):
             leilao.propor_lance(l3)
        l4 = Lance(self.p1, 80)
        leilao.propor_lance(l4)
        self.assertEqual(self.sistema.obter_maior_lance_leilao("LeilaoMM"), l4)
        self.assertEqual(self.sistema.obter_menor_lance_leilao("LeilaoMM"), l1)

    def test_obter_maior_menor_lance_sem_lances(self):
        leilao = self.sistema.cadastrar_leilao("LeilaoMMVazio", 50, self.ontem_dt, self.amanha_dt)
        self.assertIsNone(self.sistema.obter_maior_lance_leilao("LeilaoMMVazio"))
        self.assertIsNone(self.sistema.obter_menor_lance_leilao("LeilaoMMVazio"))

    def test_obter_maior_menor_lance_leilao_inexistente(self):
        with self.assertRaisesRegex(LeilaoInvalido, r"Leilão com nome \'Inexistente\' não encontrado."):
            self.sistema.obter_maior_lance_leilao("Inexistente")
        with self.assertRaisesRegex(LeilaoInvalido, r"Leilão com nome \'Inexistente\' não encontrado."):
            self.sistema.obter_menor_lance_leilao("Inexistente")

    def test_obter_ganhador_leilao_finalizado(self):
        inicio_leilao = self.anteontem_dt
        fim_leilao = self.ontem_dt
        tempo_lance = inicio_leilao + timedelta(hours=1)
        with freeze_time(inicio_leilao - timedelta(hours=1)):
            leilao = self.sistema.cadastrar_leilao("LeilaoGanhador", 50, inicio_leilao, fim_leilao)
            self.assertEqual(leilao.estado, EstadoLeilao.INATIVO, "Deveria ser INATIVO antes do início")
        with freeze_time(tempo_lance):
            leilao = self.sistema.buscar_leilao_por_nome("LeilaoGanhador")
            leilao.atualizar_estado()
            self.assertEqual(leilao.estado, EstadoLeilao.ABERTO, "Leilão deveria estar ABERTO para receber lances")
            self.sistema.propor_lance_sistema(self.p1.cpf, "LeilaoGanhador", 60)
            self.sistema.propor_lance_sistema(self.p2.cpf, "LeilaoGanhador", 70)
        with freeze_time(fim_leilao + timedelta(hours=1)):
            leilao = self.sistema.buscar_leilao_por_nome("LeilaoGanhador")
            leilao.atualizar_estado()
            self.assertEqual(leilao.estado, EstadoLeilao.FINALIZADO, "Leilão deveria estar FINALIZADO com lance")
            self.assertEqual(self.sistema.obter_ganhador_leilao("LeilaoGanhador"), self.p2)

    @freeze_time("2025-05-23 10:00:00")
    def test_obter_ganhador_leilao_nao_finalizado(self):
        leilao_aberto = self.sistema.cadastrar_leilao("AbertoGanha", 50, self.ontem_dt, self.amanha_dt)
        leilao_expirado = self.sistema.cadastrar_leilao("ExpiradoGanha", 50, self.anteontem_dt, self.ontem_dt)
        leilao_aberto.atualizar_estado()
        leilao_expirado.atualizar_estado()
        self.assertIsNone(self.sistema.obter_ganhador_leilao("AbertoGanha"))
        self.assertIsNone(self.sistema.obter_ganhador_leilao("ExpiradoGanha"))

    def test_obter_ganhador_leilao_inexistente(self):
        with self.assertRaisesRegex(LeilaoInvalido, r"Leilão com nome \'Inexistente\' não encontrado."):
            self.sistema.obter_ganhador_leilao("Inexistente")

    # --- Testes de Notificação ---
    @patch("sys.stdout", new_callable=StringIO)
    def test_notificar_ganhador_sucesso(self, mock_stdout):
        inicio_leilao = self.anteontem_dt
        fim_leilao = self.ontem_dt
        tempo_lance = inicio_leilao + timedelta(hours=1)
        with freeze_time(inicio_leilao - timedelta(hours=1)):
            leilao = self.sistema.cadastrar_leilao("LeilaoNotifica", 50, inicio_leilao, fim_leilao)
            self.assertEqual(leilao.estado, EstadoLeilao.INATIVO, "Deveria ser INATIVO antes do início")
        with freeze_time(tempo_lance):
            leilao = self.sistema.buscar_leilao_por_nome("LeilaoNotifica")
            leilao.atualizar_estado()
            self.assertEqual(leilao.estado, EstadoLeilao.ABERTO, "Leilão deveria estar ABERTO para receber lances")
            self.sistema.propor_lance_sistema(self.p1.cpf, "LeilaoNotifica", 60)
            self.sistema.propor_lance_sistema(self.p2.cpf, "LeilaoNotifica", 70)
        with freeze_time(fim_leilao + timedelta(hours=1)):
            leilao = self.sistema.buscar_leilao_por_nome("LeilaoNotifica")
            leilao.atualizar_estado()
            self.assertEqual(leilao.estado, EstadoLeilao.FINALIZADO, "Leilão deveria estar FINALIZADO para notificar")
            self.assertTrue(self.sistema.notificar_ganhador("LeilaoNotifica"))
            output = mock_stdout.getvalue()
            self.assertIn("--- SIMULAÇÃO DE EMAIL ---", output)
            self.assertIn(f"Para: {self.p2.email}", output)
            self.assertIn("Parabéns! Você arrematou o item \'LeilaoNotifica\' com o lance de R$ 70.00.", output)
            self.assertIn(f"Prezado(a) {self.p2.nome}", output)
            self.assertIn("R$ 70.00", output)

    @freeze_time("2025-05-23 10:00:00")
    @patch("sys.stdout", new_callable=StringIO)
    def test_notificar_ganhador_leilao_nao_finalizado(self, mock_stdout):
        leilao_aberto = self.sistema.cadastrar_leilao("AbertoNotifica", 50, self.ontem_dt, self.amanha_dt)
        leilao_aberto.atualizar_estado()
        self.assertFalse(self.sistema.notificar_ganhador("AbertoNotifica"))
        expected_output = "INFO: Leilão \'AbertoNotifica\' ainda não foi finalizado (Estado: ABERTO). Nenhuma notificação enviada.\n"
        self.assertEqual(mock_stdout.getvalue(), expected_output)

    @freeze_time("2025-05-23 10:00:00")
    @patch("sys.stdout", new_callable=StringIO)
    def test_notificar_ganhador_leilao_expirado(self, mock_stdout):
        leilao_expirado = self.sistema.cadastrar_leilao("ExpiradoNotifica", 50, self.anteontem_dt, self.ontem_dt)
        leilao_expirado.atualizar_estado()
        self.assertFalse(self.sistema.notificar_ganhador("ExpiradoNotifica"))
        expected_output = "INFO: Leilão \'ExpiradoNotifica\' ainda não foi finalizado (Estado: EXPIRADO). Nenhuma notificação enviada.\n"
        self.assertEqual(mock_stdout.getvalue(), expected_output)

    def test_notificar_ganhador_leilao_inexistente(self):
         with self.assertRaisesRegex(LeilaoInvalido, r"Leilão com nome \'Inexistente\' não encontrado para notificação."):
            self.sistema.notificar_ganhador("Inexistente")

    # Testes para cobrir linhas 226-227 e 230-231 de sistema.py (cenários improváveis)
    # Revisado para usar manipulação direta de atributos internos
    @patch("sys.stdout", new_callable=StringIO)
    def test_notificar_ganhador_finalizado_sem_ganhador(self, mock_stdout):
        leilao = self.sistema.cadastrar_leilao("FinalizadoSemGanhador", 50, self.anteontem_dt, self.ontem_dt)
        # Adiciona um lance diretamente na lista interna
        lance = Lance(self.p1, 60)
        leilao._lances.append(lance)
        # Força o estado FINALIZADO e remove o ganhador manualmente
        leilao._estado = EstadoLeilao.FINALIZADO
        leilao._ganhador = None
        self.assertFalse(self.sistema.notificar_ganhador("FinalizadoSemGanhador"))
        expected_output = "AVISO: Leilão \'FinalizadoSemGanhador\' está FINALIZADO mas não possui ganhador definido.\n"
        self.assertEqual(mock_stdout.getvalue(), expected_output)

    @patch("sys.stdout", new_callable=StringIO)
    def test_notificar_ganhador_com_ganhador_sem_maior_lance(self, mock_stdout):
        leilao = self.sistema.cadastrar_leilao("GanhadorSemMaiorLance", 50, self.anteontem_dt, self.ontem_dt)
        # Adiciona um lance diretamente na lista interna
        lance = Lance(self.p1, 60)
        leilao._lances.append(lance)
        # Força o estado FINALIZADO e o ganhador
        leilao._estado = EstadoLeilao.FINALIZADO
        leilao._ganhador = self.p1
        # Mocka a property maior_lance para retornar None
        with patch.object(Leilao, 'maior_lance', new_callable=PropertyMock, return_value=None):
            self.assertFalse(self.sistema.notificar_ganhador("GanhadorSemMaiorLance"))
            expected_output = "AVISO: Leilão \'GanhadorSemMaiorLance\' tem ganhador mas não foi possível obter o maior lance.\n"
            self.assertEqual(mock_stdout.getvalue(), expected_output)

if __name__ == "__main__":
    unittest.main()

