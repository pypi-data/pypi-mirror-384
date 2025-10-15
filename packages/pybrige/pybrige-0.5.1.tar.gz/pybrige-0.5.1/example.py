# Testando o estilo de atalho
from pybrige import setup_logging, print_table, __version__
import logging

print(f"A executar pybrige versão {__version__}")

# Testando o estilo de namespace
from pybrige import text

# Configura o logging
setup_logging(colors=True)

logging.info("Teste de importações híbridas iniciado.")

# Usa a função de atalho
dados = [{"nome": text.slugify("João Silva"), "status": "ativo"}]
print_table(dados, title="Relatório de Teste")

logging.info("Teste concluído com sucesso!")