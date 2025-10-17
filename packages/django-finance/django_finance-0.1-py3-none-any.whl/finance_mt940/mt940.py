import mt940
from finance.models import BankStatement


class InvalidMT940FileError(Exception):
    pass


def process_mt940_file(order_account, mt940_file):
    print (type(mt940_file))

    try:
        transactions = mt940.parse(mt940_file)
    except:
        msg = f'Could not parse {mt940_file}.'
        raise InvalidMT940FileError(msg)

    if not transactions:
        msg = f'Could not parse {mt940_file}.'
        raise InvalidMT940FileError(msg)

    created = list()
    found = list()
    for transaction in transactions:
        data = transaction.data.copy()

        statement = BankStatement()
        statement.order_account = order_account
        statement.amount = data['amount'].amount
        statement.currency = data['currency']
        statement.additional_purpose = data['additional_purpose'] or str()
        statement.posting_text = data['posting_text'] or str()
        statement.applicant_name = data['applicant_name'] or str()
        statement.applicant_iban = data['applicant_iban'] or str()
        statement.applicant_bic = data['applicant_bin'] or str()
        statement.entry_date = data['entry_date']
        statement.date = data['date']
        statement.data = data

        try:
            statement = BankStatement.objects.get(checksum=statement.get_checksum())
        except BankStatement.DoesNotExist:
            statement.save()
            created.append(statement)
        else:
            found.append(statement)

    return created, found
