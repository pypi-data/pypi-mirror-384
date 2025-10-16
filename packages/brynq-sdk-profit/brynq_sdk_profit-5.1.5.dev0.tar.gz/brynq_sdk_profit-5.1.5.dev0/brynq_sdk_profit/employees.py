"""
Employee Management Module for AFAS Integration

This module provides comprehensive employee management functionality for AFAS Profit.
It follows a handler-based architecture where each employee component (contract, function,
salary, etc.) has its own dedicated handler accessible as a property of the main Employees class.

Main Class:
-----------
Employees: The main entry point for all employee operations

Available Handlers:
------------------
- employee.contract - Manage employee contracts
- employee.function - Manage organizational functions
- employee.salary - Manage salary information
- employee.timetable - Manage work timetables
- employee.bankaccount - Manage bank accounts (supports multiple accounts)
- employee.instance - Manage agency/fiscus instances
- employee.person - Connect employees to existing persons

Supported Operations:
--------------------
1. CREATE NEW EMPLOYEE WITH ALL COMPONENTS
   df = pd.DataFrame([{
       'employee_id': 'EMP001',
       'status': 'I',  # In dienst
       'first_name': 'John',
       'last_name': 'Doe',
       'start_date_contract': date(2024, 1, 1),
       'cao': 'basis',
       'organisational_unit': 'SALES',
       # ... other fields
   }])
   afas.employee.create(df)  # POST /connectors/KnEmployee

2. UPDATE EMPLOYEE BASE FIELDS
   df = pd.DataFrame([{'employee_id': 'EMP001', 'phone_work': '+31-20-123-4567'}])
   afas.employee.update(df)  # PUT /connectors/KnEmployee

3. CREATE/UPDATE CONTRACT
   df = pd.DataFrame([{
       'employee_id': 'EMP001',
       'start_date_contract': date(2024, 1, 1),
       'cao': 'basis',
       'contract_type': 'O'
   }])
   afas.employee.contract.create(df)  # POST /connectors/KnEmployee/AfasContract
   afas.employee.contract.update(df)  # PUT /connectors/KnEmployee

4. CREATE/UPDATE FUNCTION
   df = pd.DataFrame([{
       'employee_id': 'EMP001',
       'start_date_function': date(2024, 1, 1),
       'organisational_unit': 'SALES',
       'function_id': 'MANAGER'
   }])
   afas.employee.function.create(df)  # POST /connectors/KnEmployee/AfasOrgunitFunction
   afas.employee.function.update(df)  # PUT /connectors/KnEmployee

5. CREATE/UPDATE SALARY
   df = pd.DataFrame([{
       'employee_id': 'EMP001',
       'salary_start_date': date(2024, 1, 1),
       'salary_type': 'M',
       'salary_amount': 5000
   }])
   afas.employee.salary.create(df)  # POST /connectors/KnEmployee/AfasSalary
   afas.employee.salary.update(df)  # PUT /connectors/KnEmployee

6. CREATE/UPDATE TIMETABLE
   df = pd.DataFrame([{
       'employee_id': 'EMP001',
       'timetable_start_date': date(2024, 1, 1),
       'days_per_week': 5,
       'hours_per_week': 40
   }])
   afas.employee.timetable.create(df)  # POST /connectors/KnEmployee/AfasTimeTable
   afas.employee.timetable.update(df)  # PUT /connectors/KnEmployee

7. CREATE/UPDATE BANK ACCOUNTS (supports multiple accounts)
   # Single account
   df = pd.DataFrame([{
       'employee_id': 'EMP001',
       'iban': 'NL40INGB0755026802',
       'is_salary_account': True
   }])
   afas.employee.bankaccount.create(df)  # POST /connectors/KnEmployee/AfasBankInfo

   # Multiple accounts in one operation
   accounts = [
       {'employee_id': 'EMP001', 'iban': 'NL57RABO0312000111', 'action': 'update'},
       {'employee_id': 'EMP001', 'iban': 'NL40BOTK0755026802', 'action': 'insert'}
   ]
   afas.employee.bankaccount.create(accounts)

8. CREATE/UPDATE INSTANCE (Agency/Fiscus)
   df = pd.DataFrame([{
       'employee_id': 'EMP001',
       'start_date': date(2024, 1, 1),
       'agency_id': 'F',  # Fiscus
       'income_relation_type': '15'
   }])
   afas.employee.instance.create(df)  # POST /connectors/KnEmployee/AfasAgencyFiscus
   afas.employee.instance.update(df)  # PUT /connectors/KnEmployee

9. CONNECT EMPLOYEE TO EXISTING PERSON
   df = pd.DataFrame([{
       'employee_id': 'EMP002',
       'person_id': '123456',  # Existing person
       'status': 'I',
       'start_date_contract': date(2024, 1, 1)
   }])
   afas.employee.person.connect(df)  # POST /connectors/KnEmployee

10. HIRE/REHIRE EMPLOYEE
    df = pd.DataFrame([{...employee data...}])
    afas.employee.hire(df)    # Sets status='I', blocked=False
    afas.employee.rehire(df)  # Also increments service_number

11. TERMINATE EMPLOYEE
    df = pd.DataFrame([{
        'employee_id': 'EMP001',
        'start_date_contract': date(2023, 1, 1),
        'end_date_contract': date(2024, 12, 31),
        'termination_date': date(2024, 12, 31),
        'termination_reason': '01'
    }])
    afas.employee.terminate(df)  # PUT /connectors/KnEmployee

12. GET EMPLOYEE DATA
    # Get all employees
    df = afas.employee.get()

    # Get filtered employees
    df = afas.employee.get(filter_fields={'employee_id': 'EMP001'})

Data Input Formats:
------------------
All methods accept the following input formats:
- pandas.DataFrame (can have multiple rows for bankaccount.create)
- pandas.Series (single record)
- dict (single record)
- list[dict] (only for bankaccount operations)

Field Name Conventions:
----------------------
The module accepts both AFAS field names (with aliases) and human-readable names.
For example, both 'EmId' and 'employee_id' are accepted.

Error Handling:
--------------
All methods raise descriptive exceptions on failure:
- ValueError for missing required fields
- Exception with details for API errors

Schema Validation:
-----------------
All data is validated against Pydantic schemas before being sent to AFAS,
ensuring type safety and data integrity.
"""

import asyncio
import pandas as pd
import requests
from typing import Optional, Union, Dict, Any, List
from datetime import date

from .schemas.employee import (
    EmployeeGetSchema,
    AfasEmployeePayload,
    AfasEmployeeObject,
    AfasEmployeeElement,
    EmployeeCreate,
    PersonPayload,
    AfasContractSchema,
    AfasContractObject,
    AfasContractElement,
    AfasOrgunitFunctionSchema,
    AfasOrgunitFunctionObject,
    AfasOrgunitFunctionElement,
    AfasTimeTableSchema,
    AfasTimeTableObject,
    AfasTimeTableElement,
    AfasSalarySchema,
    AfasSalaryObject,
    AfasSalaryElement,
    AfasAgencyFiscusSchema,
    AfasAgencyFiscusObject,
    AfasAgencyFiscusElement,
    AfasSalaryAdditionSchema,
    AfasWorkTimeSchema
)
from .schemas.contract import ContractCreate
from .schemas.function import FunctionCreate
from .schemas.timetable import TimeTableCreate, WorkTimeCreate
from .schemas.salary import SalaryCreate, SalaryAdditionCreate
from .schemas.agency_fiscus import AgencyFiscusCreate
from .schemas.bank_account import (
    PostBankAccountEmployee,
    AfasBankInfoElement,
    AfasBankInfo,
    AfasBankInfoObject
)
from .schemas.person import PostKnPersonFieldsSchema

from .family import Family
from .leaves import Leaves
from .sick_leaves import SickLeaves
from .address import Address
from .contract import Contract
from .functions import EmployeeFunction
from .salaries import Salaries
from .wage_mutations import WageMutations
from .wage_components import WageComponents
from .payslips import Payslips


class EmployeeContractHandler:
    """Handler for employee contract operations"""

    def __init__(self, employee_instance):
        self.employee = employee_instance
        self.afas = employee_instance.afas

    def create(self, data: Union[pd.DataFrame, pd.Series, dict], *, return_meta: bool = True) -> Optional[dict]:
        """Create contract for an employee"""
        try:
            # Convert DataFrame/Series to dict
            if isinstance(data, pd.DataFrame):
                if len(data) > 1:
                    raise ValueError("Only one row allowed for contract create")
                data = data.iloc[0].to_dict()
            elif isinstance(data, pd.Series):
                data = data.to_dict()

            # Extract employee_id and start_date
            employee_id = data.get('employee_id')
            start_date = data.get('start_date_contract', data.get('contract_start_date'))

            if not employee_id:
                raise ValueError("employee_id is required")
            if not start_date:
                raise ValueError("start_date_contract is required")

            # Create contract fields
            contract_fields = ContractCreate(**data)

            # Build nested structure
            payload = AfasEmployeePayload(
                afas_employee=AfasEmployeeObject(
                    element=AfasEmployeeElement(
                        employee_identifier=employee_id,
                        fields=EmployeeCreate(),
                        objects=[
                            AfasContractSchema(
                                afas_contract=AfasContractObject(
                                    element=[
                                        AfasContractElement(
                                            contract_start_date=start_date,
                                            fields=contract_fields
                                        )
                                    ]
                                )
                            )
                        ]
                    )
                )
            )

            payload_dict = payload.model_dump(by_alias=True, mode="json", exclude_none=True)
            # Add action for nested element
            payload_dict["AfasEmployee"]["Element"]["@Action"] = "update"
            payload_dict["AfasEmployee"]["Element"]["Objects"][0]["AfasContract"]["Element"][0]["@Action"] = "insert"

            return self.afas.base_post("KnEmployee/AfasContract", payload_dict, return_meta=return_meta)
        except Exception as e:
            raise Exception(f"Create contract failed: {str(e)}") from e

    def update(self, data: Union[pd.DataFrame, pd.Series, dict], *, return_meta: bool = True) -> Optional[dict]:
        """Update contract for an employee"""
        try:
            # Convert DataFrame/Series to dict
            if isinstance(data, pd.DataFrame):
                if len(data) > 1:
                    raise ValueError("Only one row allowed for contract update")
                data = data.iloc[0].to_dict()
            elif isinstance(data, pd.Series):
                data = data.to_dict()

            # Extract employee_id and start_date
            employee_id = data.get('employee_id')
            start_date = data.get('start_date_contract', data.get('contract_start_date'))

            if not employee_id:
                raise ValueError("employee_id is required")
            if not start_date:
                raise ValueError("start_date_contract is required")

            # Create contract fields
            contract_fields = ContractCreate(**data)

            # Build nested structure
            payload = AfasEmployeePayload(
                afas_employee=AfasEmployeeObject(
                    element=AfasEmployeeElement(
                        employee_identifier=employee_id,
                        fields=EmployeeCreate(),
                        objects=[
                            AfasContractSchema(
                                afas_contract=AfasContractObject(
                                    element=[
                                        AfasContractElement(
                                            contract_start_date=start_date,
                                            fields=contract_fields
                                        )
                                    ]
                                )
                            )
                        ]
                    )
                )
            )

            payload_dict = payload.model_dump(by_alias=True, mode="json", exclude_none=True)
            # Add action for nested element
            payload_dict["AfasEmployee"]["Element"]["@Action"] = "update"

            # Convert Element array to object for update operations
            if "Objects" in payload_dict["AfasEmployee"]["Element"] and payload_dict["AfasEmployee"]["Element"]["Objects"]:
                contract_obj = payload_dict["AfasEmployee"]["Element"]["Objects"][0]["AfasContract"]
                if "Element" in contract_obj and isinstance(contract_obj["Element"], list) and len(contract_obj["Element"]) > 0:
                    contract_obj["Element"] = contract_obj["Element"][0]
                    contract_obj["Element"]["@Action"] = "update"

            return self.afas.base_put("KnEmployee", payload_dict, return_meta=return_meta)
        except Exception as e:
            raise Exception(f"Update contract failed: {str(e)}") from e


class EmployeeFunctionHandler:
    """Handler for employee function operations"""

    def __init__(self, employee_instance):
        self.employee = employee_instance
        self.afas = employee_instance.afas

    def create(self, data: Union[pd.DataFrame, pd.Series, dict], *, return_meta: bool = True) -> Optional[dict]:
        """Create function for an employee"""
        try:
            # Convert DataFrame/Series to dict
            if isinstance(data, pd.DataFrame):
                if len(data) > 1:
                    raise ValueError("Only one row allowed for function create")
                data = data.iloc[0].to_dict()
            elif isinstance(data, pd.Series):
                data = data.to_dict()

            # Extract employee_id and start_date
            employee_id = data.get('employee_id')
            start_date = data.get('start_date_function', data.get('function_start_date'))

            if not employee_id:
                raise ValueError("employee_id is required")
            if not start_date:
                raise ValueError("start_date_function is required")

            # Create function fields
            function_fields = FunctionCreate(**data)

            # Build nested structure
            payload = AfasEmployeePayload(
                afas_employee=AfasEmployeeObject(
                    element=AfasEmployeeElement(
                        employee_identifier=employee_id,
                        fields=EmployeeCreate(),
                        objects=[
                            AfasOrgunitFunctionSchema(
                                afas_orgunit_function=AfasOrgunitFunctionObject(
                                    element=[
                                        AfasOrgunitFunctionElement(
                                            start_date_attribute=start_date,
                                            fields=function_fields
                                        )
                                    ]
                                )
                            )
                        ]
                    )
                )
            )

            payload_dict = payload.model_dump(by_alias=True, mode="json", exclude_none=True)
            payload_dict["AfasEmployee"]["Element"]["@Action"] = "update"
            payload_dict["AfasEmployee"]["Element"]["Objects"][0]["AfasOrgunitFunction"]["Element"][0]["@Action"] = "insert"

            return self.afas.base_post("KnEmployee/AfasOrgunitFunction", payload_dict, return_meta=return_meta)
        except Exception as e:
            raise Exception(f"Create function failed: {str(e)}") from e

    def update(self, data: Union[pd.DataFrame, pd.Series, dict], *, return_meta: bool = True) -> Optional[dict]:
        """Update function for an employee"""
        try:
            # Convert DataFrame/Series to dict
            if isinstance(data, pd.DataFrame):
                if len(data) > 1:
                    raise ValueError("Only one row allowed for function update")
                data = data.iloc[0].to_dict()
            elif isinstance(data, pd.Series):
                data = data.to_dict()

            # Extract employee_id and start_date
            employee_id = data.get('employee_id')
            start_date = data.get('start_date_function', data.get('function_start_date'))

            if not employee_id:
                raise ValueError("employee_id is required")
            if not start_date:
                raise ValueError("start_date_function is required")

            # Create function fields
            function_fields = FunctionCreate(**data)

            # Build nested structure
            payload = AfasEmployeePayload(
                afas_employee=AfasEmployeeObject(
                    element=AfasEmployeeElement(
                        employee_identifier=employee_id,
                        fields=EmployeeCreate(),
                        objects=[
                            AfasOrgunitFunctionSchema(
                                afas_orgunit_function=AfasOrgunitFunctionObject(
                                    element=[
                                        AfasOrgunitFunctionElement(
                                            start_date_attribute=start_date,
                                            fields=function_fields
                                        )
                                    ]
                                )
                            )
                        ]
                    )
                )
            )

            payload_dict = payload.model_dump(by_alias=True, mode="json", exclude_none=True)
            payload_dict["AfasEmployee"]["Element"]["@Action"] = "update"

            # Convert Element array to object for update operations
            if "Objects" in payload_dict["AfasEmployee"]["Element"] and payload_dict["AfasEmployee"]["Element"]["Objects"]:
                function_obj = payload_dict["AfasEmployee"]["Element"]["Objects"][0]["AfasOrgunitFunction"]
                if "Element" in function_obj and isinstance(function_obj["Element"], list) and len(function_obj["Element"]) > 0:
                    function_obj["Element"] = function_obj["Element"][0]
                    function_obj["Element"]["@Action"] = "update"

            return self.afas.base_put("KnEmployee", payload_dict, return_meta=return_meta)
        except Exception as e:
            raise Exception(f"Update function failed: {str(e)}") from e


class EmployeeSalaryHandler:
    """Handler for employee salary operations"""

    def __init__(self, employee_instance):
        self.employee = employee_instance
        self.afas = employee_instance.afas

    def create(self, data: Union[pd.DataFrame, pd.Series, dict], *, return_meta: bool = True) -> Optional[dict]:
        """Create salary for an employee"""
        try:
            # Convert DataFrame/Series to dict
            if isinstance(data, pd.DataFrame):
                if len(data) > 1:
                    raise ValueError("Only one row allowed for salary create")
                data = data.iloc[0].to_dict()
            elif isinstance(data, pd.Series):
                data = data.to_dict()

            # Extract employee_id and start_date
            employee_id = data.get('employee_id')
            start_date = data.get('salary_start_date', data.get('start_date_salary'))

            if not employee_id:
                raise ValueError("employee_id is required")
            if not start_date:
                raise ValueError("salary_start_date is required")

            # Create salary fields
            salary_fields = SalaryCreate(**data)

            # Build nested structure
            payload = AfasEmployeePayload(
                afas_employee=AfasEmployeeObject(
                    element=AfasEmployeeElement(
                        employee_identifier=employee_id,
                        fields=EmployeeCreate(),
                        objects=[
                            AfasSalarySchema(
                                afas_salary=AfasSalaryObject(
                                    element=[
                                        AfasSalaryElement(
                                            salary_start_date=start_date,
                                            fields=salary_fields
                                        )
                                    ]
                                )
                            )
                        ]
                    )
                )
            )

            payload_dict = payload.model_dump(by_alias=True, mode="json", exclude_none=True)
            payload_dict["AfasEmployee"]["Element"]["@Action"] = "update"
            payload_dict["AfasEmployee"]["Element"]["Objects"][0]["AfasSalary"]["Element"][0]["@Action"] = "insert"

            return self.afas.base_post("KnEmployee/AfasSalary", payload_dict, return_meta=return_meta)
        except Exception as e:
            raise Exception(f"Create salary failed: {str(e)}") from e

    def update(self, data: Union[pd.DataFrame, pd.Series, dict], *, return_meta: bool = True) -> Optional[dict]:
        """Update salary for an employee"""
        try:
            # Convert DataFrame/Series to dict
            if isinstance(data, pd.DataFrame):
                if len(data) > 1:
                    raise ValueError("Only one row allowed for salary update")
                data = data.iloc[0].to_dict()
            elif isinstance(data, pd.Series):
                data = data.to_dict()

            # Extract employee_id and start_date
            employee_id = data.get('employee_id')
            start_date = data.get('salary_start_date', data.get('start_date_salary'))

            if not employee_id:
                raise ValueError("employee_id is required")
            if not start_date:
                raise ValueError("salary_start_date is required")

            # Create salary fields
            salary_fields = SalaryCreate(**data)

            # Build nested structure
            payload = AfasEmployeePayload(
                afas_employee=AfasEmployeeObject(
                    element=AfasEmployeeElement(
                        employee_identifier=employee_id,
                        fields=EmployeeCreate(),
                        objects=[
                            AfasSalarySchema(
                                afas_salary=AfasSalaryObject(
                                    element=[
                                        AfasSalaryElement(
                                            salary_start_date=start_date,
                                            fields=salary_fields
                                        )
                                    ]
                                )
                            )
                        ]
                    )
                )
            )

            payload_dict = payload.model_dump(by_alias=True, mode="json", exclude_none=True)
            payload_dict["AfasEmployee"]["Element"]["@Action"] = "update"

            # Convert Element array to object for update operations
            if "Objects" in payload_dict["AfasEmployee"]["Element"] and payload_dict["AfasEmployee"]["Element"]["Objects"]:
                salary_obj = payload_dict["AfasEmployee"]["Element"]["Objects"][0]["AfasSalary"]
                if "Element" in salary_obj and isinstance(salary_obj["Element"], list) and len(salary_obj["Element"]) > 0:
                    salary_obj["Element"] = salary_obj["Element"][0]
                    salary_obj["Element"]["@Action"] = "update"

            return self.afas.base_put("KnEmployee", payload_dict, return_meta=return_meta)
        except Exception as e:
            raise Exception(f"Update salary failed: {str(e)}") from e


class EmployeeTimetableHandler:
    """Handler for employee timetable operations"""

    def __init__(self, employee_instance):
        self.employee = employee_instance
        self.afas = employee_instance.afas

    def create(self, data: Union[pd.DataFrame, pd.Series, dict], *, return_meta: bool = True) -> Optional[dict]:
        """Create timetable for an employee"""
        try:
            # Convert DataFrame/Series to dict
            if isinstance(data, pd.DataFrame):
                if len(data) > 1:
                    raise ValueError("Only one row allowed for timetable create")
                data = data.iloc[0].to_dict()
            elif isinstance(data, pd.Series):
                data = data.to_dict()

            # Extract employee_id and start_date
            employee_id = data.get('employee_id')
            start_date = data.get('timetable_start_date', data.get('start_date_timetable'))

            if not employee_id:
                raise ValueError("employee_id is required")
            if not start_date:
                raise ValueError("timetable_start_date is required")

            # Create timetable fields
            timetable_fields = TimeTableCreate(**data)

            # Build nested structure
            payload = AfasEmployeePayload(
                afas_employee=AfasEmployeeObject(
                    element=AfasEmployeeElement(
                        employee_identifier=employee_id,
                        fields=EmployeeCreate(),
                        objects=[
                            AfasTimeTableSchema(
                                afas_time_table=AfasTimeTableObject(
                                    element=[
                                        AfasTimeTableElement(
                                            timetable_start_date=start_date,
                                            fields=timetable_fields
                                        )
                                    ]
                                )
                            )
                        ]
                    )
                )
            )

            payload_dict = payload.model_dump(by_alias=True, mode="json", exclude_none=True)
            payload_dict["AfasEmployee"]["Element"]["@Action"] = "update"
            payload_dict["AfasEmployee"]["Element"]["Objects"][0]["AfasTimeTable"]["Element"][0]["@Action"] = "insert"

            return self.afas.base_post("KnEmployee/AfasTimeTable", payload_dict, return_meta=return_meta)
        except Exception as e:
            raise Exception(f"Create timetable failed: {str(e)}") from e

    def update(self, data: Union[pd.DataFrame, pd.Series, dict], *, return_meta: bool = True) -> Optional[dict]:
        """Update timetable for an employee"""
        try:
            # Convert DataFrame/Series to dict
            if isinstance(data, pd.DataFrame):
                if len(data) > 1:
                    raise ValueError("Only one row allowed for timetable update")
                data = data.iloc[0].to_dict()
            elif isinstance(data, pd.Series):
                data = data.to_dict()

            # Extract employee_id and start_date
            employee_id = data.get('employee_id')
            start_date = data.get('timetable_start_date', data.get('start_date_timetable'))

            if not employee_id:
                raise ValueError("employee_id is required")
            if not start_date:
                raise ValueError("timetable_start_date is required")

            # Create timetable fields
            timetable_fields = TimeTableCreate(**data)

            # Build nested structure
            payload = AfasEmployeePayload(
                afas_employee=AfasEmployeeObject(
                    element=AfasEmployeeElement(
                        employee_identifier=employee_id,
                        fields=EmployeeCreate(),
                        objects=[
                            AfasTimeTableSchema(
                                afas_time_table=AfasTimeTableObject(
                                    element=[
                                        AfasTimeTableElement(
                                            timetable_start_date=start_date,
                                            fields=timetable_fields
                                        )
                                    ]
                                )
                            )
                        ]
                    )
                )
            )

            payload_dict = payload.model_dump(by_alias=True, mode="json", exclude_none=True)
            payload_dict["AfasEmployee"]["Element"]["@Action"] = "update"

            # Convert Element array to object for update operations
            if "Objects" in payload_dict["AfasEmployee"]["Element"] and payload_dict["AfasEmployee"]["Element"]["Objects"]:
                timetable_obj = payload_dict["AfasEmployee"]["Element"]["Objects"][0]["AfasTimeTable"]
                if "Element" in timetable_obj and isinstance(timetable_obj["Element"], list) and len(timetable_obj["Element"]) > 0:
                    timetable_obj["Element"] = timetable_obj["Element"][0]
                    timetable_obj["Element"]["@Action"] = "update"

            return self.afas.base_put("KnEmployee", payload_dict, return_meta=return_meta)
        except Exception as e:
            raise Exception(f"Update timetable failed: {str(e)}") from e


class EmployeeBankAccountHandler:
    """Handler for employee bank account operations"""

    def __init__(self, employee_instance):
        self.employee = employee_instance
        self.afas = employee_instance.afas

    def create(self, data: Union[pd.DataFrame, pd.Series, dict, List[dict]], *, return_meta: bool = True) -> Optional[dict]:
        """
        Create bank account(s) for an employee.
        Can handle single account or multiple accounts in one operation.
        """
        try:
            # Handle multiple formats
            accounts = []
            employee_id = None

            if isinstance(data, pd.DataFrame):
                # Convert DataFrame to list of dicts
                accounts = data.to_dict('records')
                if accounts:
                    employee_id = accounts[0].get('employee_id')
            elif isinstance(data, pd.Series):
                accounts = [data.to_dict()]
                employee_id = data.get('employee_id')
            elif isinstance(data, dict):
                accounts = [data]
                employee_id = data.get('employee_id')
            elif isinstance(data, list):
                accounts = data
                if accounts:
                    employee_id = accounts[0].get('employee_id')

            if not employee_id:
                raise ValueError("employee_id is required")

            # Build bank account elements using schemas
            bank_elements = []
            for account in accounts:
                # Create bank account fields
                bank_fields = PostBankAccountEmployee(**account)

                # Create element with attributes
                bank_element = AfasBankInfoElement(
                    fields=bank_fields,
                    account_id_attr=account.get('account_id', account.get('iban', '')),
                    no_bank_attr=account.get('is_cash_payment', False),
                    action=account.get('action', 'insert')
                )
                bank_elements.append(bank_element)

            # Build payload using schemas
            from .schemas.bank_account import BankAccountEmployeePayload, BankAccountEmployee, BankAccountEmployeeElement

            afas_bank_info = AfasBankInfo(element=bank_elements)
            afas_bank_info_object = AfasBankInfoObject(afas_bank_info=afas_bank_info)

            employee_element = BankAccountEmployeeElement(
                objects=[afas_bank_info_object],
                employee_id=employee_id,
                action="update"
            )

            bank_account_employee = BankAccountEmployee(element=employee_element)
            payload_model = BankAccountEmployeePayload(afas_employee=bank_account_employee)

            # Serialize using schema
            payload_dict = payload_model.model_dump(by_alias=True, mode="json", exclude_none=True)

            return self.afas.base_post("KnEmployee/AfasBankInfo", payload_dict, return_meta=return_meta)
        except Exception as e:
            raise Exception(f"Create bank account failed: {str(e)}") from e

    def update(self, data: Union[pd.DataFrame, pd.Series, dict, List[dict]], *, return_meta: bool = True) -> Optional[dict]:
        """
        Update bank account(s) for an employee.
        Can handle single account or multiple accounts in one operation.
        """
        try:
            # Handle multiple formats
            accounts = []
            employee_id = None

            if isinstance(data, pd.DataFrame):
                accounts = data.to_dict('records')
                if accounts:
                    employee_id = accounts[0].get('employee_id')
            elif isinstance(data, pd.Series):
                accounts = [data.to_dict()]
                employee_id = data.get('employee_id')
            elif isinstance(data, dict):
                accounts = [data]
                employee_id = data.get('employee_id')
            elif isinstance(data, list):
                accounts = data
                if accounts:
                    employee_id = accounts[0].get('employee_id')

            if not employee_id:
                raise ValueError("employee_id is required")

            # Build bank account elements using schemas
            bank_elements = []
            for account in accounts:
                # Create bank account fields
                bank_fields = PostBankAccountEmployee(**account)

                # Create element with attributes
                bank_element = AfasBankInfoElement(
                    fields=bank_fields,
                    account_id_attr=account.get('account_id', account.get('iban', '')),
                    no_bank_attr=account.get('is_cash_payment', False),
                    action=account.get('action', 'update')
                )
                bank_elements.append(bank_element)

            # Build payload using schemas
            from .schemas.bank_account import BankAccountEmployeePayload, BankAccountEmployee, BankAccountEmployeeElement

            afas_bank_info = AfasBankInfo(element=bank_elements)
            afas_bank_info_object = AfasBankInfoObject(afas_bank_info=afas_bank_info)

            employee_element = BankAccountEmployeeElement(
                objects=[afas_bank_info_object],
                employee_id=employee_id,
                action="update"
            )

            bank_account_employee = BankAccountEmployee(element=employee_element)
            payload_model = BankAccountEmployeePayload(afas_employee=bank_account_employee)

            # Serialize using schema
            payload_dict = payload_model.model_dump(by_alias=True, mode="json", exclude_none=True)

            return self.afas.base_put("KnEmployee", payload_dict, return_meta=return_meta)
        except Exception as e:
            raise Exception(f"Update bank account failed: {str(e)}") from e


class PersonConnectionHandler:
    """Handler for connecting employee to existing person"""

    def __init__(self, employee_instance):
        self.employee = employee_instance
        self.afas = employee_instance.afas

    def connect(self, data: Union[pd.DataFrame, pd.Series, dict], *, return_meta: bool = True) -> Optional[dict]:
        """
        Create new employee connected to an existing person.

        This creates a new employee record linked to an existing person,
        including all necessary components (contract, function, etc.)
        """
        try:
            # Convert DataFrame/Series to dict
            if isinstance(data, pd.DataFrame):
                if len(data) > 1:
                    raise ValueError("Only one row allowed for person connect")
                data = data.iloc[0].to_dict()
            elif isinstance(data, pd.Series):
                data = data.to_dict()

            # Extract required fields
            employee_id = data.get('employee_id')
            person_id = data.get('person_id')

            if not employee_id:
                raise ValueError("employee_id is required")
            if not person_id:
                raise ValueError("person_id is required for connecting to existing person")

            # Create employee fields
            employee_fields = EmployeeCreate(**data)

            # Build nested objects list
            objects = []

            # Add person connection with MatchPer=0 to match on person_id
            person_data = {
                "match_person": "0",  # Match on person_id
                "person_id": person_id
            }
            from .schemas.person import PostKnPersonFieldsSchema
            person_fields = PostKnPersonFieldsSchema(**person_data)
            objects.append(
                PersonPayload(
                    kn_person={
                        "element": {
                            "fields": person_fields
                        }
                    }
                )
            )

            # Add contract if contract data is provided
            if any(key in data for key in ['start_date_contract', 'contract_type', 'cao']):
                start_date = data.get('start_date_contract')
                if start_date:
                    contract_fields = ContractCreate(**data)
                    objects.append(
                        AfasContractSchema(
                            afas_contract=AfasContractObject(
                                element=[
                                    AfasContractElement(
                                        action="insert",
                                        contract_start_date=start_date,
                                        fields=contract_fields
                                    )
                                ]
                            )
                        )
                    )

            # Add function if function data is provided
            if any(key in data for key in ['organisational_unit', 'function_id', 'start_date_function']):
                start_date = data.get('start_date_function')
                if start_date:
                    function_fields = FunctionCreate(**data)
                    objects.append(
                        AfasOrgunitFunctionSchema(
                            afas_orgunit_function=AfasOrgunitFunctionObject(
                                element=[
                                    AfasOrgunitFunctionElement(
                                        action="insert",
                                        start_date_attribute=start_date,
                                        fields=function_fields
                                    )
                                ]
                            )
                        )
                    )

            # Add other components as needed...
            # (timetable, salary, bank account, agency fiscus)

            # Build final payload
            payload = AfasEmployeePayload(
                afas_employee=AfasEmployeeObject(
                    element=AfasEmployeeElement(
                        action="insert",
                        employee_identifier=employee_id,
                        fields=employee_fields,
                        objects=objects if objects else None
                    )
                )
            )

            payload_dict = payload.model_dump(by_alias=True, mode="json", exclude_none=True)

            # CRITICAL FIX: Convert Objects from array to dictionary as AFAS expects
            # AFAS API requires Objects to be a dictionary, not an array
            if "Objects" in payload_dict["AfasEmployee"]["Element"] and isinstance(payload_dict["AfasEmployee"]["Element"]["Objects"], list):
                objects_list = payload_dict["AfasEmployee"]["Element"]["Objects"]
                objects_dict = {}
                for obj in objects_list:
                    # Each object has a single key (KnPerson, AfasContract, etc.)
                    # Merge all object dictionaries into one
                    objects_dict.update(obj)
                payload_dict["AfasEmployee"]["Element"]["Objects"] = objects_dict

            return self.afas.base_post("KnEmployee", payload_dict, return_meta=return_meta)
        except Exception as e:
            raise Exception(f"Connect person failed: {str(e)}") from e

    def create(self, data: Union[pd.DataFrame, pd.Series, dict], *, return_meta: bool = True) -> Optional[dict]:
        """
        Create both person and employee records in a single operation.

        Accepts all person fields (first_name, last_name, etc.) plus minimal employee fields.
        This is used when you know someone will need employment data from the start.

        Args:
            data: Dictionary containing both person fields and employee fields
            return_meta: Whether to return metadata

        Returns:
            Optional[dict]: Response from AFAS API
        """
        try:
            # Convert DataFrame/Series to dict
            if isinstance(data, pd.DataFrame):
                if len(data) > 1:
                    raise ValueError("Only one row allowed for person create")
                data = data.iloc[0].to_dict()
            elif isinstance(data, pd.Series):
                data = data.to_dict()

            # Dynamically determine person fields from schema
            person_field_names = set(PostKnPersonFieldsSchema.model_fields.keys())

            # Also check Python field names (not just aliases)
            # Some fields might be passed with Python names instead of AFAS aliases
            python_to_alias_map = {
                field_name: field_info.alias
                for field_name, field_info in PostKnPersonFieldsSchema.model_fields.items()
                if field_info.alias
            }
            alias_to_python_map = {v: k for k, v in python_to_alias_map.items()}

            # All valid person field identifiers (both Python names and aliases)
            # EXCLUDE 'employee_id' as it's needed for the main employee element (EmId)
            # even though it also exists in person schema with different meaning (BcId)
            all_person_field_identifiers = (person_field_names | set(python_to_alias_map.values())) - {'employee_id'}

            # Extract person data (prefer person schema for overlapping fields)
            person_data = {
                k: v for k, v in data.items()
                if k in all_person_field_identifiers
                and v is not None
                and str(v).strip() != ''
            }

            # Extract employee data (everything else that's not person-specific)
            # This will include employee_id which is needed for the main element
            employee_data = {
                k: v for k, v in data.items()
                if k not in all_person_field_identifiers
            }

            # Extract employee_id (required)
            employee_id = employee_data.get('employee_id')
            if not employee_id:
                raise ValueError("employee_id is required")

            # Create employee fields (minimal - only what's actually employee-specific)
            # Remove employee_id from the data that goes to EmployeeCreate
            employee_fields_data = {k: v for k, v in employee_data.items() if k != 'employee_id'}
            employee_fields = EmployeeCreate(**employee_fields_data) if employee_fields_data else EmployeeCreate()

            # Build nested objects as a list (for schema validation)
            # The schema will serialize this correctly
            objects = []

            # Add person data as nested object (without person_id or match_person for creation)
            if person_data:
                person_fields_obj = PostKnPersonFieldsSchema(**person_data)
                objects.append(
                    PersonPayload(
                        kn_person={
                            "element": {
                                "fields": person_fields_obj
                            }
                        }
                    )
                )

            # Add contract if contract data is provided
            if any(key in data for key in ['start_date_contract', 'contract_type', 'cao']):
                start_date = data.get('start_date_contract')
                if start_date:
                    contract_fields = ContractCreate(**data)
                    objects.append(
                        AfasContractSchema(
                            afas_contract=AfasContractObject(
                                element=[
                                    AfasContractElement(
                                        action="insert",
                                        contract_start_date=start_date,
                                        fields=contract_fields
                                    )
                                ]
                            )
                        )
                    )

            # Add function if function data is provided
            if any(key in data for key in ['organisational_unit', 'function_id', 'start_date_function']):
                start_date = data.get('start_date_function')
                if start_date:
                    function_fields = FunctionCreate(**data)
                    objects.append(
                        AfasOrgunitFunctionSchema(
                            afas_orgunit_function=AfasOrgunitFunctionObject(
                                element=[
                                    AfasOrgunitFunctionElement(
                                        action="insert",
                                        start_date_attribute=start_date,
                                        fields=function_fields
                                    )
                                ]
                            )
                        )
                    )

            # Build final payload
            payload = AfasEmployeePayload(
                afas_employee=AfasEmployeeObject(
                    element=AfasEmployeeElement(
                        action="insert",
                        employee_identifier=employee_id,
                        fields=employee_fields,
                        objects=objects if objects else None
                    )
                )
            )

            payload_dict = payload.model_dump(by_alias=True, mode="json", exclude_none=True)

            # CRITICAL FIX: Convert Objects from array to dictionary as AFAS expects
            # AFAS API requires Objects to be a dictionary, not an array
            if "Objects" in payload_dict["AfasEmployee"]["Element"] and isinstance(payload_dict["AfasEmployee"]["Element"]["Objects"], list):
                objects_list = payload_dict["AfasEmployee"]["Element"]["Objects"]
                objects_dict = {}
                for obj in objects_list:
                    # Each object has a single key (KnPerson, AfasContract, etc.)
                    # Merge all object dictionaries into one
                    objects_dict.update(obj)
                payload_dict["AfasEmployee"]["Element"]["Objects"] = objects_dict

            return self.afas.base_post("KnEmployee", payload_dict, return_meta=return_meta)
        except Exception as e:
            raise Exception(f"Create person and employee failed: {str(e)}") from e


class EmployeeInstanceHandler:
    """Handler for employee instance (AfasAgencyFiscus) operations"""

    def __init__(self, employee_instance):
        self.employee = employee_instance
        self.afas = employee_instance.afas

    def create(self, data: Union[pd.DataFrame, pd.Series, dict], *, return_meta: bool = True) -> Optional[dict]:
        """Create instance for an employee"""
        try:
            # Convert DataFrame/Series to dict
            if isinstance(data, pd.DataFrame):
                if len(data) > 1:
                    raise ValueError("Only one row allowed for instance create")
                data = data.iloc[0].to_dict()
            elif isinstance(data, pd.Series):
                data = data.to_dict()

            # Extract required fields
            employee_id = data.get('employee_id')
            start_date = data.get('start_date', data.get('instance_start_date'))
            agency_id = data.get('agency_id', 'F')  # Default to 'F' for Fiscus

            if not employee_id:
                raise ValueError("employee_id is required")
            if not start_date:
                raise ValueError("start_date is required")

            # Create agency fiscus fields
            agency_fields = AgencyFiscusCreate(**data)

            # Build nested structure using schemas
            agency_element = AfasAgencyFiscusElement(
                start_date_attr=start_date,
                agency_id_attr=agency_id,
                action="insert",
                fields=agency_fields
            )

            # Build payload
            payload = AfasEmployeePayload(
                afas_employee=AfasEmployeeObject(
                    element=AfasEmployeeElement(
                        action="update",
                        employee_identifier=employee_id,
                        fields=EmployeeCreate(),
                        objects=[
                            AfasAgencyFiscusSchema(
                                afas_agency_fiscus=AfasAgencyFiscusObject(
                                    element=[agency_element]
                                )
                            )
                        ]
                    )
                )
            )

            payload_dict = payload.model_dump(by_alias=True, mode="json", exclude_none=True)

            # Convert Element array to object for update operations
            if "Objects" in payload_dict["AfasEmployee"]["Element"] and payload_dict["AfasEmployee"]["Element"]["Objects"]:
                agency_obj = payload_dict["AfasEmployee"]["Element"]["Objects"][0]["AfasAgencyFiscus"]
                if "Element" in agency_obj and isinstance(agency_obj["Element"], list) and len(agency_obj["Element"]) > 0:
                    agency_obj["Element"] = agency_obj["Element"][0]

            return self.afas.base_post("KnEmployee/AfasAgencyFiscus", payload_dict, return_meta=return_meta)
        except Exception as e:
            raise Exception(f"Create instance failed: {str(e)}") from e

    def update(self, data: Union[pd.DataFrame, pd.Series, dict], *, return_meta: bool = True) -> Optional[dict]:
        """Update instance for an employee"""
        try:
            # Convert DataFrame/Series to dict
            if isinstance(data, pd.DataFrame):
                if len(data) > 1:
                    raise ValueError("Only one row allowed for instance update")
                data = data.iloc[0].to_dict()
            elif isinstance(data, pd.Series):
                data = data.to_dict()

            # Extract required fields
            employee_id = data.get('employee_id')
            start_date = data.get('start_date', data.get('instance_start_date'))
            agency_id = data.get('agency_id', 'F')  # Default to 'F' for Fiscus

            if not employee_id:
                raise ValueError("employee_id is required")
            if not start_date:
                raise ValueError("start_date is required")

            # Create agency fiscus fields
            agency_fields = AgencyFiscusCreate(**data)

            # Build nested structure using schemas
            agency_element = AfasAgencyFiscusElement(
                start_date_attr=start_date,
                agency_id_attr=agency_id,
                action="update",
                fields=agency_fields
            )

            # Build payload
            payload = AfasEmployeePayload(
                afas_employee=AfasEmployeeObject(
                    element=AfasEmployeeElement(
                        action="update",
                        employee_identifier=employee_id,
                        fields=EmployeeCreate(),
                        objects=[
                            AfasAgencyFiscusSchema(
                                afas_agency_fiscus=AfasAgencyFiscusObject(
                                    element=[agency_element]
                                )
                            )
                        ]
                    )
                )
            )

            payload_dict = payload.model_dump(by_alias=True, mode="json", exclude_none=True)

            # Convert Element array to object for update operations
            if "Objects" in payload_dict["AfasEmployee"]["Element"] and payload_dict["AfasEmployee"]["Element"]["Objects"]:
                agency_obj = payload_dict["AfasEmployee"]["Element"]["Objects"][0]["AfasAgencyFiscus"]
                if "Element" in agency_obj and isinstance(agency_obj["Element"], list) and len(agency_obj["Element"]) > 0:
                    agency_obj["Element"] = agency_obj["Element"][0]

            return self.afas.base_put("KnEmployee", payload_dict, return_meta=return_meta)
        except Exception as e:
            raise Exception(f"Update instance failed: {str(e)}") from e


class Employees:
    """Employee management class for AFAS integration"""

    def __init__(self, afas_connector):
        """
        Initialize Employees class with AFAS connector

        Args:
            afas_connector: AFAS connection handler instance
        """
        self.afas = afas_connector
        self.address = Address(afas_connector)
        self.leaves = Leaves(afas_connector)
        self.sick_leaves = SickLeaves(afas_connector)
        self.family = Family(afas_connector)
        self.payslips = Payslips(afas_connector)
        self.wage_components = WageComponents(afas_connector)
        self.wage_mutations = WageMutations(afas_connector)
        self.get_url = f"{self.afas.base_url}/brynq_sdk_employee_actual_data"

        # Handler instances
        self._contract_handler = None
        self._function_handler = None
        self._salary_handler = None
        self._timetable_handler = None
        self._bankaccount_handler = None
        self._instance_handler = None
        self._person_handler = None

    @property
    def contract(self):
        """Get contract handler for employee-specific contract operations"""
        if self._contract_handler is None:
            self._contract_handler = EmployeeContractHandler(self)
        return self._contract_handler

    @property
    def function(self):
        """Get function handler for employee-specific function operations"""
        if self._function_handler is None:
            self._function_handler = EmployeeFunctionHandler(self)
        return self._function_handler

    @property
    def salary(self):
        """Get salary handler for employee-specific salary operations"""
        if self._salary_handler is None:
            self._salary_handler = EmployeeSalaryHandler(self)
        return self._salary_handler

    @property
    def timetable(self):
        """Get timetable handler for employee-specific timetable operations"""
        if self._timetable_handler is None:
            self._timetable_handler = EmployeeTimetableHandler(self)
        return self._timetable_handler

    @property
    def bankaccount(self):
        """Get bank account handler for employee-specific bank account operations"""
        if self._bankaccount_handler is None:
            self._bankaccount_handler = EmployeeBankAccountHandler(self)
        return self._bankaccount_handler

    @property
    def instance(self):
        """Get instance handler for employee-specific instance (AfasAgencyFiscus) operations"""
        if self._instance_handler is None:
            self._instance_handler = EmployeeInstanceHandler(self)
        return self._instance_handler

    @property
    def person(self):
        """Get person connection handler for linking employees to existing persons"""
        if self._person_handler is None:
            self._person_handler = PersonConnectionHandler(self)
        return self._person_handler

    def get(self, filter_fields: dict = None) -> pd.DataFrame:
        """
        Get employee information from AFAS

        Args:
            filter_fields (dict, optional): Dictionary of filters in format {field_name: value}

        Returns:
            pd.DataFrame: DataFrame containing employee information

        Raises:
            Exception: If get employee operation fails
        """
        try:
            return asyncio.run(self.afas.base_get(url=self.get_url, schema=EmployeeGetSchema, filter_fields=filter_fields))
        except Exception as e:
            raise Exception(f"Get employee failed: {str(e)}") from e

    def create(self, data: Union[pd.DataFrame, pd.Series, dict], *, return_meta: bool = True) -> Optional[dict]:
        """
        Create an employee with all nested components in AFAS.

        Args:
            data: Employee data as DataFrame, Series, or dict
            return_meta: Whether to return metadata

        Returns:
            Optional[dict]: Response from AFAS API
        """
        try:
            # Convert DataFrame/Series to dict
            if isinstance(data, pd.DataFrame):
                if len(data) > 1:
                    raise ValueError("Only one row allowed for employee create")
                data = data.iloc[0].to_dict()
            elif isinstance(data, pd.Series):
                data = data.to_dict()

            # Extract employee fields and nested objects
            employee_id = data.get('employee_id')
            if not employee_id:
                raise ValueError("employee_id is required")

            # Create employee fields
            employee_fields = EmployeeCreate(**data)

            # Build nested objects list
            objects = []

            # Add KnPerson if person data is provided
            if any(key in data for key in ['first_name', 'last_name', 'person_id']):
                from .schemas.person import PostKnPersonFieldsSchema
                person_fields = PostKnPersonFieldsSchema(**data)
                objects.append(
                    PersonPayload(
                        kn_person={
                            "element": {
                                "fields": person_fields,
                                "objects": []
                            }
                        }
                    )
                )

            # Add contract if contract data is provided
            if any(key in data for key in ['start_date_contract', 'contract_type', 'cao']):
                start_date = data.get('start_date_contract')
                if start_date:
                    contract_fields = ContractCreate(**data)
                    objects.append(
                        AfasContractSchema(
                            afas_contract=AfasContractObject(
                                element=[
                                    AfasContractElement(
                                        contract_start_date=start_date,
                                        fields=contract_fields
                                    )
                                ]
                            )
                        )
                    )

            # Add function if function data is provided
            if any(key in data for key in ['organisational_unit', 'function_id', 'start_date_function']):
                start_date = data.get('start_date_function')
                if start_date:
                    function_fields = FunctionCreate(**data)
                    objects.append(
                        AfasOrgunitFunctionSchema(
                            afas_orgunit_function=AfasOrgunitFunctionObject(
                                element=[
                                    AfasOrgunitFunctionElement(
                                        start_date_attribute=start_date,
                                        fields=function_fields
                                    )
                                ]
                            )
                        )
                    )

            # Add timetable if timetable data is provided
            if any(key in data for key in ['timetable_start_date', 'schedule_type', 'days_per_week', 'hours_per_week']):
                start_date = data.get('timetable_start_date')
                if start_date:
                    timetable_fields = TimeTableCreate(**data)
                    objects.append(
                        AfasTimeTableSchema(
                            afas_time_table=AfasTimeTableObject(
                                element=[
                                    AfasTimeTableElement(
                                        timetable_start_date=start_date,
                                        fields=timetable_fields
                                    )
                                ]
                            )
                        )
                    )

            # Add salary if salary data is provided
            if any(key in data for key in ['salary_start_date', 'salary_type', 'salary_amount']):
                start_date = data.get('salary_start_date')
                if start_date:
                    salary_fields = SalaryCreate(**data)
                    objects.append(
                        AfasSalarySchema(
                            afas_salary=AfasSalaryObject(
                                element=[
                                    AfasSalaryElement(
                                        salary_start_date=start_date,
                                        fields=salary_fields
                                    )
                                ]
                            )
                        )
                    )

            # Add agency fiscus if instance data is provided
            if any(key in data for key in ['income_relation_type', 'employment_relation_type', 'tax_table_color']):
                start_date = data.get('start_date', data.get('instance_start_date'))
                agency_id = data.get('agency_id', 'F')
                if start_date:
                    agency_fields = AgencyFiscusCreate(**data)
                    objects.append(
                        AfasAgencyFiscusSchema(
                            afas_agency_fiscus=AfasAgencyFiscusObject(
                                element=[
                                    AfasAgencyFiscusElement(
                                        fields=agency_fields
                                    )
                                ]
                            )
                        )
                    )

            # Build final payload
            payload = AfasEmployeePayload(
                afas_employee=AfasEmployeeObject(
                    element=AfasEmployeeElement(
                        action="insert",
                        employee_identifier=employee_id,
                        fields=employee_fields,
                        objects=objects if objects else None
                    )
                )
            )

            payload_dict = payload.model_dump(by_alias=True, mode="json", exclude_none=True)

            return self.afas.base_post("KnEmployee", payload_dict, return_meta=return_meta)
        except Exception as e:
            raise Exception(f"Create employee failed: {str(e)}") from e

    def update(self, data: Union[pd.DataFrame, pd.Series, dict], *, return_meta: bool = True) -> Optional[dict]:
        """
        Update an employee's base fields in AFAS.

        Note: To update nested objects (contract, function, etc.), use the specific handlers:
        - employee.contract.update()
        - employee.function.update()
        - etc.

        Args:
            data: Employee data as DataFrame, Series, or dict
            return_meta: Whether to return metadata

        Returns:
            Optional[dict]: Response from AFAS API
        """
        try:
            # Convert DataFrame/Series to dict
            if isinstance(data, pd.DataFrame):
                if len(data) > 1:
                    raise ValueError("Only one row allowed for employee update")
                data = data.iloc[0].to_dict()
            elif isinstance(data, pd.Series):
                data = data.to_dict()

            # Extract employee_id
            employee_id = data.get('employee_id')
            if not employee_id:
                raise ValueError("employee_id is required")

            # Create employee fields
            employee_fields = EmployeeCreate(**data)

            # Build payload - only update employee fields, not nested objects
            payload = AfasEmployeePayload(
                afas_employee=AfasEmployeeObject(
                    element=AfasEmployeeElement(
                        action="update",
                        employee_identifier=employee_id,
                        fields=employee_fields
                    )
                )
            )

            payload_dict = payload.model_dump(by_alias=True, mode="json", exclude_none=True)

            return self.afas.base_put("KnEmployee", payload_dict, return_meta=return_meta)
        except Exception as e:
            raise Exception(f"Update employee failed: {str(e)}") from e

    def hire(self, data: Union[pd.DataFrame, pd.Series, dict], *, return_meta: bool = True) -> Optional[dict]:
        """
        Hire a new employee (alias for create with status set to 'In dienst').

        Args:
            data: Employee data as DataFrame, Series, or dict
            return_meta: Whether to return metadata

        Returns:
            Optional[dict]: Response from AFAS API
        """
        # Convert DataFrame/Series to dict
        if isinstance(data, pd.DataFrame):
            if len(data) > 1:
                raise ValueError("Only one row allowed for employee hire")
            data = data.iloc[0].to_dict()
        elif isinstance(data, pd.Series):
            data = data.to_dict()
        elif not isinstance(data, dict):
            data = dict(data)

        # Set default values for hire
        data['status'] = 'I'  # In dienst
        data['blocked'] = False

        return self.create(data, return_meta=return_meta)

    def rehire(self, data: Union[pd.DataFrame, pd.Series, dict], *, return_meta: bool = True) -> Optional[dict]:
        """
        Rehire an existing employee (create with new employment record).

        Args:
            data: Employee data as DataFrame, Series, or dict
            return_meta: Whether to return metadata

        Returns:
            Optional[dict]: Response from AFAS API
        """
        # Convert DataFrame/Series to dict
        if isinstance(data, pd.DataFrame):
            if len(data) > 1:
                raise ValueError("Only one row allowed for employee rehire")
            data = data.iloc[0].to_dict()
        elif isinstance(data, pd.Series):
            data = data.to_dict()
        elif not isinstance(data, dict):
            data = dict(data)

        # Set default values for rehire
        data['status'] = 'I'  # In dienst
        data['blocked'] = False
        # Increment service number if provided
        if 'service_number' in data:
            data['service_number'] = int(data['service_number']) + 1

        return self.create(data, return_meta=return_meta)

    def delete(self, employee_id: str) -> requests.Response:
        """
        Delete an employee from AFAS

        Args:
            employee_id: The ID of the employee to delete

        Returns:
            requests.Response: Response from AFAS API
        """
        try:
            url = f"{self.afas.base_url}/KnEmployee/AfasEmployee/@EmId/{employee_id}"
            return self.afas.session.delete(url, timeout=self.afas.timeout)
        except Exception as e:
            raise Exception(f"Delete employee failed: {str(e)}")

    def terminate(self, data: Union[pd.DataFrame, pd.Series, dict], *, return_meta: bool = True) -> Optional[dict]:
        """
        Terminate employee in AFAS by updating contract end date and termination details.

        Args:
            data: Termination data including employee_id, start_date_contract, end_date_contract, termination_date
            return_meta: Whether to return metadata

        Returns:
            Optional[dict]: Response from AFAS API
        """
        try:
            # Convert DataFrame/Series to dict
            if isinstance(data, pd.DataFrame):
                if len(data) > 1:
                    raise ValueError("Only one row allowed for employee terminate")
                data = data.iloc[0].to_dict()
            elif isinstance(data, pd.Series):
                data = data.to_dict()

            # Extract required fields
            employee_id = data.get('employee_id')
            start_date_contract = data.get('start_date_contract')
            end_date_contract = data.get('end_date_contract')
            termination_date = data.get('termination_date')

            if not employee_id:
                raise ValueError("employee_id is required")
            if not start_date_contract:
                raise ValueError("start_date_contract is required")
            if not end_date_contract:
                raise ValueError("end_date_contract is required")
            if not termination_date:
                raise ValueError("termination_date is required")

            # Build contract fields for termination
            contract_data = {
                'end_date_contract': end_date_contract,
                'out_of_service_date': termination_date
            }

            # Add optional termination fields if provided
            if 'termination_initiative' in data:
                contract_data['termination_iniative'] = data['termination_initiative']
            if 'termination_reason' in data:
                contract_data['termination_reason'] = data['termination_reason']
            if 'reason_end_of_employment' in data:
                contract_data['dvb_reason_end_contract'] = data['reason_end_of_employment']

            contract_fields = ContractCreate(**contract_data)

            # Build nested structure
            payload = AfasEmployeePayload(
                afas_employee=AfasEmployeeObject(
                    element=AfasEmployeeElement(
                        action="update",
                        employee_identifier=employee_id,
                        fields=EmployeeCreate(),
                        objects=[
                            AfasContractSchema(
                                afas_contract=AfasContractObject(
                                    element=[
                                        AfasContractElement(
                                            contract_start_date=start_date_contract,
                                            fields=contract_fields
                                        )
                                    ]
                                )
                            )
                        ]
                    )
                )
            )

            payload_dict = payload.model_dump(by_alias=True, mode="json", exclude_none=True)

            # Convert Element array to object for update operations
            if "Objects" in payload_dict["AfasEmployee"]["Element"] and payload_dict["AfasEmployee"]["Element"]["Objects"]:
                contract_obj = payload_dict["AfasEmployee"]["Element"]["Objects"][0]["AfasContract"]
                if "Element" in contract_obj and isinstance(contract_obj["Element"], list) and len(contract_obj["Element"]) > 0:
                    contract_obj["Element"] = contract_obj["Element"][0]
                    contract_obj["Element"]["@Action"] = "update"

            return self.afas.base_put("KnEmployee", payload_dict, return_meta=return_meta)
        except Exception as e:
            raise Exception(f"Employee terminate failed: {str(e)}")
