import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.sap_functions import SAP
import pytest
from dotenv import load_dotenv
import os

load_dotenv()

sap = SAP(1)

def test_transaction():
   with pytest.raises(Exception):
      sap.select_transaction(os.getenv("not_existant_transaction"))
   sap.select_transaction(os.getenv("transaction_1"))

# def test_insert_data_transation():
#    print(os.getenv("transaction_1_field_1_name"), os.getenv("transaction_1_field_1_value"))
#    sap.write_text_field(os.getenv("transaction_1_field_1_name"), os.getenv("transaction_1_field_1_value"))

# def test_run_transaction():
#    sap.run_actual_transaction()

# def test_shell():
#    shell = sap.get_shell()
#    with pytest.raises(Exception):
#       shell.select_layout(os.getenv("transaction_1_shell_not_existant_layout"))
#    shell.select_layout(os.getenv("transaction_1_shell_layout"))

   