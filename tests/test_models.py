import unittest
from datetime import date, datetime, timedelta
import sys
import os

from src.models import Participante, Lance, Leilao, EstadoLeilao
from src.exceptions import LanceInvalido, LeilaoInvalido, ParticipanteInvalido
from freezegun import freeze_time # type: ignore

class TestParticipante(unittest.TestCase):

    def test_criar_participante_valido(self):
        p = Participante("João Silva", "12345678900", "joao@example.com", date(1990, 5, 15))
        self.assertEqual(p.nome, "João Silva")
        self.assertEqual(p.cpf, "12345678900")
        self.assertEqual(p.email, "joao@example.com")
        self.assertEqual(p.data_nascimento, date(1990, 5, 15))
        self.assertTrue(p.pode_ser_excluido)

    def test_criar_participante_cpf_com_formatacao(self):
        p = Participante("Maria Oliveira", "123.456.789-00", "maria@test.net", date(1985, 1, 10))
        self.assertEqual(p.cpf, "12345678900") # Deve armazenar apenas números

    def test_criar_participante_dados_invalidos(self):
        with self.assertRaisesRegex(ValueError, "Nome inválido"):
            Participante("", "12345678900", "teste@email.com", date(2000, 1, 1))
        with self.assertRaisesRegex(ValueError, "Nome inválido"):
            Participante(None, "12345678900", "teste@email.com", date(2000, 1, 1))

        with self.assertRaisesRegex(ValueError, "CPF inválido"):
            Participante("Nome Valido", "123", "teste@email.com", date(2000, 1, 1))
        with self.assertRaisesRegex(ValueError, "CPF inválido"):
            Participante("Nome Valido", "1234567890", "teste@email.com", date(2000, 1, 1))
        with self.assertRaisesRegex(ValueError, "CPF inválido"):
            Participante("Nome Valido", "123456789000", "teste@email.com", date(2000, 1, 1))
        with self.assertRaisesRegex(ValueError, "CPF inválido"):
            Participante("Nome Valido", None, "teste@email.com", date(2000, 1, 1))

        with self.assertRaisesRegex(ValueError, "Email inválido"):
            Participante("Nome Valido", "12345678900", "teste", date(2000, 1, 1))
        with self.assertRaisesRegex(ValueError, "Email inválido"):
            Participante("Nome Valido", "12345678900", "teste@", date(2000, 1, 1))
        with self.assertRaisesRegex(ValueError, "Email inválido"):
            Participante("Nome Valido", "12345678900", "teste@domain", date(2000, 1, 1))
        with self.assertRaisesRegex(ValueError, "Email inválido"):
            Participante("Nome Valido", "12345678900", "teste@domain.", date(2000, 1, 1))
        with self.assertRaisesRegex(ValueError, "Email inválido"):
            Participante("Nome Valido", "12345678900", None, date(2000, 1, 1))

        with self.assertRaisesRegex(ValueError, "Data de nascimento inválida"):
            Participante("Nome Valido", "12345678900", "teste@email.com", "2000-01-01") # String não é date
        with self.assertRaisesRegex(ValueError, "Data de nascimento inválida"):
            Participante("Nome Valido", "12345678900", "teste@email.com", None)

    def test_participante_marcar_como_ofertante(self):
        p = Participante("Carlos Souza", "98765432100", "carlos@domain.org", date(1978, 11, 22))
        self.assertTrue(p.pode_ser_excluido)
        p.marcar_como_ofertante()
        self.assertFalse(p.pode_ser_excluido)

    def test_participante_igualdade(self):
        p1 = Participante("Ana Costa", "11122233300", "ana@mail.com", date(1995, 3, 8))
        p2 = Participante("Ana Costa Silva", "11122233300", "ana.silva@mail.com", date(1995, 3, 8))
        p3 = Participante("Beatriz Lima", "44455566600", "ana@mail.com", date(1992, 7, 1))
        p4 = Participante("Carlos Dias", "77788899900", "carlos@mail.com", date(1988, 9, 12))

        self.assertEqual(p1, p2) # Mesmo CPF
        self.assertEqual(p1, p3) # Mesmo Email
        self.assertNotEqual(p1, p4)
        self.assertNotEqual(p2, p3) # CPF e Email diferentes
        self.assertNotEqual(p1, "Não é participante") # Comparação com tipo diferente

    def test_participante_hash(self):
        p1 = Participante("Ana Costa", "11122233300", "ana@mail.com", date(1995, 3, 8))
        p2 = Participante("Ana Costa Silva", "11122233300", "ana.silva@mail.com", date(1995, 3, 8))
        p3 = Participante("Carlos Dias", "77788899900", "carlos@mail.com", date(1988, 9, 12))

        self.assertEqual(hash(p1), hash(p2)) # Hash baseado no CPF
        self.assertNotEqual(hash(p1), hash(p3))

    def test_participante_representacao_string(self):
        p = Participante("João Silva", "123.456.789-00", "joao@example.com", date(1990, 5, 15))
        self.assertEqual(str(p), "Participante(Nome: João Silva, CPF: 12345678900, Email: joao@example.com)")
        expected_repr = "Participante(nome=\'João Silva\', cpf=\'12345678900\', email=\'joao@example.com\', data_nascimento=datetime.date(1990, 5, 15))"
        self.assertEqual(repr(p), expected_repr)

class TestLance(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Criar um participante reutilizável para os testes de Lance
        cls.participante_teste = Participante("Testador", "11111111111", "testador@lance.com", date(2000, 1, 1))

    def test_criar_lance_valido(self):
        lance = Lance(self.participante_teste, 100.50)
        self.assertEqual(lance.participante, self.participante_teste)
        self.assertEqual(lance.valor, 100.50)

    def test_criar_lance_valor_inteiro(self):
        lance = Lance(self.participante_teste, 200)
        self.assertEqual(lance.valor, 200.0) # Deve converter para float

    def test_criar_lance_invalido(self):
        # Participante inválido
        with self.assertRaisesRegex(TypeError, "Participante inválido para o lance"):
            Lance("Não é participante", 100.0)
        with self.assertRaisesRegex(TypeError, "Participante inválido para o lance"):
            Lance(None, 100.0)

        # Valor inválido
        with self.assertRaisesRegex(ValueError, "O valor do lance deve ser positivo"):
            Lance(self.participante_teste, 0)
        with self.assertRaisesRegex(ValueError, "O valor do lance deve ser positivo"):
            Lance(self.participante_teste, -50.0)
        with self.assertRaisesRegex(ValueError, "O valor do lance deve ser positivo"):
            Lance(self.participante_teste, "abc") # Tipo inválido
        with self.assertRaisesRegex(ValueError, "O valor do lance deve ser positivo"):
            Lance(self.participante_teste, None)

    def test_lance_comparacao(self):
        p1 = Participante("P1", "11111111111", "p1@mail.com", date(2001,1,1))
        p2 = Participante("P2", "22222222222", "p2@mail.com", date(2002,2,2))
        lance100_p1 = Lance(p1, 100)
        lance100_p2 = Lance(p2, 100)
        lance200_p1 = Lance(p1, 200)
        lance50_p2 = Lance(p2, 50)
        lance100_p1_dup = Lance(p1, 100) # Mesmo participante e valor

        # Igualdade (==)
        self.assertEqual(lance100_p1, lance100_p1_dup)
        self.assertNotEqual(lance100_p1, lance100_p2) # Mesmo valor, participante diferente
        self.assertNotEqual(lance100_p1, lance200_p1) # Mesmo participante, valor diferente
        self.assertNotEqual(lance100_p1, "Não é lance")

        # Menor que (<)
        self.assertTrue(lance50_p2 < lance100_p1)
        self.assertTrue(lance100_p1 < lance200_p1)
        self.assertFalse(lance100_p1 < lance100_p2)
        self.assertFalse(lance100_p1 < lance50_p2)
        self.assertFalse(lance100_p1 < lance100_p1_dup)

        # Menor ou igual (<=)
        self.assertTrue(lance50_p2 <= lance100_p1)
        self.assertTrue(lance100_p1 <= lance200_p1)
        self.assertTrue(lance100_p1 <= lance100_p2)
        self.assertTrue(lance100_p1 <= lance100_p1_dup)
        self.assertFalse(lance100_p1 <= lance50_p2)

        # Maior que (>)
        self.assertTrue(lance100_p1 > lance50_p2)
        self.assertTrue(lance200_p1 > lance100_p1)
        self.assertFalse(lance100_p1 > lance100_p2)
        self.assertFalse(lance50_p2 > lance100_p1)
        self.assertFalse(lance100_p1 > lance100_p1_dup)

        # Maior ou igual (>=)
        self.assertTrue(lance100_p1 >= lance50_p2)
        self.assertTrue(lance200_p1 >= lance100_p1)
        self.assertTrue(lance100_p1 >= lance100_p2)
        self.assertTrue(lance100_p1 >= lance100_p1_dup)
        self.assertFalse(lance50_p2 >= lance100_p1)

        # Teste com tipo diferente (deve retornar NotImplemented)
        with self.assertRaises(TypeError):
            lance100_p1 < "abc"
        with self.assertRaises(TypeError):
            lance100_p1 <= "abc"
        with self.assertRaises(TypeError):
            lance100_p1 > "abc"
        with self.assertRaises(TypeError):
            lance100_p1 >= "abc"

    def test_lance_representacao_string(self):
        lance = Lance(self.participante_teste, 150.75)
        self.assertEqual(str(lance), "Lance(Participante: Testador, Valor: R$ 150.75)")
        # O repr do participante dentro do repr do lance pode variar um pouco
        self.assertTrue(repr(lance).startswith("Lance(participante=Participante(nome="))
        self.assertTrue("valor=150.75" in repr(lance))

class TestLeilao(unittest.TestCase):

    def setUp(self):
        self.participante1 = Participante("Alice", "11111111111", "alice@test.com", date(1991, 1, 1))
        self.participante2 = Participante("Bob", "22222222222", "bob@test.com", date(1992, 2, 2))
        self.agora = datetime.now()
        self.amanha = self.agora + timedelta(days=1)
        self.depois_amanha = self.agora + timedelta(days=2)
        self.ontem = self.agora - timedelta(days=1)
        self.anteontem = self.agora - timedelta(days=2)

    def test_criar_leilao_valido(self):
        leilao = Leilao("Console", 100.0, self.amanha, self.depois_amanha)
        self.assertEqual(leilao.nome, "Console")
        self.assertEqual(leilao.lance_minimo, 100.0)
        self.assertEqual(leilao.data_inicio, self.amanha)
        self.assertEqual(leilao.data_termino, self.depois_amanha)
        self.assertEqual(leilao.estado, EstadoLeilao.INATIVO) # Deve começar INATIVO
        self.assertEqual(leilao.lances, [])
        self.assertIsNone(leilao.maior_lance)
        self.assertIsNone(leilao.menor_lance)
        self.assertIsNone(leilao.ganhador)
        self.assertTrue(leilao.pode_ser_alterado_ou_excluido)

    def test_criar_leilao_dados_invalidos(self):
        with self.assertRaisesRegex(ValueError, "Nome do leilão inválido"):
            Leilao("", 100, self.amanha, self.depois_amanha)
        with self.assertRaisesRegex(ValueError, "Nome do leilão inválido"):
            Leilao(None, 100, self.amanha, self.depois_amanha)

        with self.assertRaisesRegex(ValueError, "Lance mínimo deve ser positivo"):
            Leilao("Item", 0, self.amanha, self.depois_amanha)
        with self.assertRaisesRegex(ValueError, "Lance mínimo deve ser positivo"):
            Leilao("Item", -50, self.amanha, self.depois_amanha)
        with self.assertRaisesRegex(ValueError, "Lance mínimo deve ser positivo"):
            Leilao("Item", "abc", self.amanha, self.depois_amanha)

        with self.assertRaisesRegex(ValueError, "Datas de início e término devem ser objetos datetime"):
            Leilao("Item", 100, "2025-06-01 10:00:00", self.depois_amanha)
        with self.assertRaisesRegex(ValueError, "Datas de início e término devem ser objetos datetime"):
            Leilao("Item", 100, self.amanha, None)

        with self.assertRaisesRegex(ValueError, "Data de início deve ser anterior à data de término"):
            Leilao("Item", 100, self.depois_amanha, self.amanha)
        with self.assertRaisesRegex(ValueError, "Data de início deve ser anterior à data de término"):
            Leilao("Item", 100, self.amanha, self.amanha)

    @freeze_time("2025-05-23 12:00:00")
    def test_estado_inicial_inativo(self):
        # Leilão começa amanhã
        leilao = Leilao("Futuro", 50, datetime(2025, 5, 24, 10, 0, 0), datetime(2025, 5, 25, 10, 0, 0))
        self.assertEqual(leilao.estado, EstadoLeilao.INATIVO)
        self.assertTrue(leilao.pode_ser_alterado_ou_excluido)

    @freeze_time("2025-05-23 12:00:00")
    def test_estado_inicial_aberto(self):
        # Leilão começou ontem e termina amanhã
        leilao = Leilao("Em Andamento", 50, datetime(2025, 5, 22, 10, 0, 0), datetime(2025, 5, 24, 10, 0, 0))
        self.assertEqual(leilao.estado, EstadoLeilao.ABERTO)
        self.assertFalse(leilao.pode_ser_alterado_ou_excluido)

    @freeze_time("2025-05-23 12:00:00")
    def test_estado_inicial_expirado_sem_lances(self):
        # Leilão terminou ontem, sem lances
        leilao = Leilao("Passado Sem Lances", 50, datetime(2025, 5, 21, 10, 0, 0), datetime(2025, 5, 22, 10, 0, 0))
        self.assertEqual(leilao.estado, EstadoLeilao.EXPIRADO)
        self.assertTrue(leilao.pode_ser_alterado_ou_excluido)
        self.assertIsNone(leilao.ganhador)

    def test_propor_lance_valido_primeiro(self):
        leilao = Leilao("Item Aberto", 100, self.ontem, self.amanha)
        lance = Lance(self.participante1, 110.0)
        leilao.propor_lance(lance)
        self.assertEqual(len(leilao.lances), 1)
        self.assertEqual(leilao.ultimo_lance, lance)
        self.assertEqual(leilao.maior_lance, lance)
        self.assertEqual(leilao.menor_lance, lance)
        self.assertFalse(self.participante1.pode_ser_excluido) # Participante agora tem lance

    def test_propor_lance_valido_segundo_maior(self):
        leilao = Leilao("Item Aberto", 100, self.ontem, self.amanha)
        lance1 = Lance(self.participante1, 110.0)
        leilao.propor_lance(lance1)
        lance2 = Lance(self.participante2, 120.0)
        leilao.propor_lance(lance2)
        self.assertEqual(len(leilao.lances), 2)
        self.assertEqual(leilao.ultimo_lance, lance2)
        self.assertEqual(leilao.maior_lance, lance2)
        self.assertEqual(leilao.menor_lance, lance1)
        self.assertEqual(leilao.lances, [lance1, lance2]) # Ordenado por valor

    def test_propor_lance_invalido_leilao_nao_aberto(self):
        leilao_inativo = Leilao("Inativo", 100, self.amanha, self.depois_amanha)
        leilao_expirado = Leilao("Expirado", 100, self.anteontem, self.ontem)
        leilao_finalizado = Leilao("Finalizado", 100, self.anteontem, self.ontem)
        # Forçar finalização com um lance
        lance_finalizador = Lance(self.participante1, 110)
        with freeze_time(self.anteontem + timedelta(hours=1)):
             leilao_finalizado._estado = EstadoLeilao.ABERTO # Força abertura para aceitar lance
             leilao_finalizado.propor_lance(lance_finalizador)
        with freeze_time(self.agora):
             leilao_finalizado.atualizar_estado() # Deve ir para FINALIZADO
             self.assertEqual(leilao_finalizado.estado, EstadoLeilao.FINALIZADO)

        lance = Lance(self.participante2, 150)

        with self.assertRaisesRegex(LeilaoInvalido, "não está ABERTO para receber lances \\(Estado: INATIVO\\)"):
            leilao_inativo.propor_lance(lance)
        with self.assertRaisesRegex(LeilaoInvalido, "não está ABERTO para receber lances \\(Estado: EXPIRADO\\)"):
            leilao_expirado.propor_lance(lance)
        with self.assertRaisesRegex(LeilaoInvalido, "não está ABERTO para receber lances \\(Estado: FINALIZADO\\)"):
            leilao_finalizado.propor_lance(lance)

    def test_propor_lance_invalido_valor_baixo(self):
        leilao = Leilao("Item Aberto", 100, self.ontem, self.amanha)
        # Abaixo do mínimo
        lance_baixo = Lance(self.participante1, 90)
        with self.assertRaisesRegex(LanceInvalido, "valor \\(R\\$ 90.00\\) abaixo do mínimo \\(R\\$ 100.00\\)"):
            leilao.propor_lance(lance_baixo)

        # Igual ao mínimo (ok para primeiro lance)
        lance_minimo = Lance(self.participante1, 100)
        leilao.propor_lance(lance_minimo)
        self.assertEqual(leilao.ultimo_lance, lance_minimo)

        # Menor que o último lance (e também abaixo do mínimo neste caso)
        lance_menor_ultimo = Lance(self.participante2, 95)
        # O código verifica primeiro se está abaixo do mínimo.
        with self.assertRaisesRegex(LanceInvalido, "valor \\(R\\$ 95.00\\) abaixo do mínimo \\(R\\$ 100.00\\)"):
            leilao.propor_lance(lance_menor_ultimo)

        # Igual ao último lance
        lance_igual_ultimo = Lance(self.participante2, 100)
        with self.assertRaisesRegex(LanceInvalido, "valor \\(R\\$ 100.00\\) não é maior que o último lance \\(R\\$ 100.00\\)"):
            leilao.propor_lance(lance_igual_ultimo)

    def test_propor_lance_invalido_mesmo_participante_seguido(self):
        leilao = Leilao("Item Aberto", 100, self.ontem, self.amanha)
        lance1 = Lance(self.participante1, 110)
        leilao.propor_lance(lance1)
        lance2 = Lance(self.participante1, 120)
        with self.assertRaisesRegex(LanceInvalido, "participante não pode dar dois lances seguidos"):
            leilao.propor_lance(lance2)

        # Deve ser possível se outro participante der lance no meio
        lance_outro = Lance(self.participante2, 115)
        leilao.propor_lance(lance_outro)
        lance3 = Lance(self.participante1, 120) # Agora válido
        leilao.propor_lance(lance3)
        self.assertEqual(leilao.ultimo_lance, lance3)

    def test_propor_lance_invalido_objeto_lance_errado(self):
        leilao = Leilao("Item Aberto", 100, self.ontem, self.amanha)
        with self.assertRaisesRegex(TypeError, "Objeto de lance inválido"):
            leilao.propor_lance("Não é um lance")

    @freeze_time("2025-05-20 12:00:00") # Antes do início
    def test_transicao_inativo_para_aberto(self):
        leilao = Leilao("Transição", 100, datetime(2025, 5, 21, 10, 0, 0), datetime(2025, 5, 22, 10, 0, 0))
        self.assertEqual(leilao.estado, EstadoLeilao.INATIVO)
        with freeze_time("2025-05-21 10:00:00"): # Exatamente no início
            self.assertEqual(leilao.estado, EstadoLeilao.ABERTO)
        with freeze_time("2025-05-21 15:00:00"): # Durante o leilão
            self.assertEqual(leilao.estado, EstadoLeilao.ABERTO)
            self.assertFalse(leilao.pode_ser_alterado_ou_excluido)

    @freeze_time("2025-05-21 15:00:00") # Durante o leilão
    def test_transicao_aberto_para_finalizado(self):
        leilao = Leilao("Transição Final", 100, datetime(2025, 5, 21, 10, 0, 0), datetime(2025, 5, 22, 10, 0, 0))
        self.assertEqual(leilao.estado, EstadoLeilao.ABERTO)
        lance1 = Lance(self.participante1, 110)
        leilao.propor_lance(lance1)
        lance2 = Lance(self.participante2, 120)
        leilao.propor_lance(lance2)

        with freeze_time("2025-05-22 09:59:59"): # Um segundo antes do fim
            self.assertEqual(leilao.estado, EstadoLeilao.ABERTO)
            self.assertIsNone(leilao.ganhador)

        with freeze_time("2025-05-22 10:00:00"): # Exatamente no fim
            self.assertEqual(leilao.estado, EstadoLeilao.FINALIZADO)
            self.assertEqual(leilao.ganhador, self.participante2) # Ganhador é o do maior lance
            self.assertFalse(leilao.pode_ser_alterado_ou_excluido)

        with freeze_time("2025-05-22 11:00:00"): # Depois do fim
            self.assertEqual(leilao.estado, EstadoLeilao.FINALIZADO)
            self.assertEqual(leilao.ganhador, self.participante2)

    @freeze_time("2025-05-21 15:00:00") # Durante o leilão
    def test_transicao_aberto_para_expirado(self):
        leilao = Leilao("Transição Expira", 100, datetime(2025, 5, 21, 10, 0, 0), datetime(2025, 5, 22, 10, 0, 0))
        self.assertEqual(leilao.estado, EstadoLeilao.ABERTO)
        # Nenhum lance é feito

        with freeze_time("2025-05-22 09:59:59"): # Um segundo antes do fim
            self.assertEqual(leilao.estado, EstadoLeilao.ABERTO)

        with freeze_time("2025-05-22 10:00:00"): # Exatamente no fim
            self.assertEqual(leilao.estado, EstadoLeilao.EXPIRADO)
            self.assertIsNone(leilao.ganhador)
            self.assertTrue(leilao.pode_ser_alterado_ou_excluido)

        with freeze_time("2025-05-22 11:00:00"): # Depois do fim
            self.assertEqual(leilao.estado, EstadoLeilao.EXPIRADO)

    def test_lances_propriedade_ordenada(self):
        leilao = Leilao("Ordenado", 50, self.ontem, self.amanha)
        lance1 = Lance(self.participante1, 100)
        lance2 = Lance(self.participante2, 80)
        lance3 = Lance(self.participante1, 120)
        lance4 = Lance(self.participante2, 110)

        leilao.propor_lance(lance1)
        # Lance 2 é inválido, menor que anterior - não será adicionado
        with self.assertRaises(LanceInvalido):
             leilao.propor_lance(lance2)

        leilao.propor_lance(lance4) # Válido (p2, 110 > 100)
        leilao.propor_lance(lance3) # Válido (p1, 120 > 110)

        # Lances esperados na ordem de valor: 100, 110, 120
        lances_esperados = [lance1, lance4, lance3]
        self.assertEqual(leilao.lances, lances_esperados)
        self.assertEqual(leilao.maior_lance, lance3)
        self.assertEqual(leilao.menor_lance, lance1)

    def test_leilao_representacao_string(self):
        leilao = Leilao("Console X", 150.0, self.amanha, self.depois_amanha)
        self.assertEqual(str(leilao), "Leilão(Nome: Console X, Estado: INATIVO, Lances: 0)")
        expected_repr = (f"Leilao(nome=\'Console X\', lance_minimo=150.0, "
                         f"data_inicio={self.amanha!r}, data_termino={self.depois_amanha!r})")
        self.assertEqual(repr(leilao), expected_repr)

if __name__ == '__main__':
    # Para executar os testes diretamente deste arquivo (útil para debug)
    # Adiciona o diretório pai (leilao_system) ao path para encontrar 'src'
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    unittest.main()

