from django.core.management.base import BaseCommand
from apps.accounts.models import Account
from apps.accounts.services import AccountService


class Command(BaseCommand):
    help = 'Start all active accounts'

    def add_arguments(self, parser):
        parser.add_argument(
            '--account-id',
            type=int,
            help='Start specific account by ID',
        )

    def handle(self, *args, **options):
        if options['account_id']:
            try:
                account = Account.objects.get(id=options['account_id'])
                if AccountService.start_account(account):
                    self.stdout.write(
                        self.style.SUCCESS(f'Started account {account.phone_number}')
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(f'Failed to start account {account.phone_number}')
                    )
            except Account.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Account with ID {options["account_id"]} not found')
                )
        else:
            accounts = Account.objects.filter(status='active')
            started = 0
            
            for account in accounts:
                if AccountService.start_account(account):
                    started += 1
                    self.stdout.write(f'Started account {account.phone_number}')
                else:
                    self.stdout.write(
                        self.style.ERROR(f'Failed to start account {account.phone_number}')
                    )
            
            self.stdout.write(
                self.style.SUCCESS(f'Started {started} out of {accounts.count()} accounts')
            )