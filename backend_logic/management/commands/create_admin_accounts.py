"""
Django management command to create pre-configured admin accounts with different roles
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from backend_logic.models import BursaryApplication, UserProfile
from django.db import transaction


class Command(BaseCommand):
    help = 'Creates pre-configured admin accounts for bursary application verification'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Reset existing accounts (WARNING: This will delete and recreate accounts)',
        )

    def handle(self, *args, **options):
        reset = options.get('reset', False)

        # Define admin accounts with roles
        admin_accounts = [
            {
                'username': 'super_admin',
                'email': 'admin@westpokot.go.ke',
                'password': 'WPBursary@2024!',
                'first_name': 'Super',
                'last_name': 'Administrator',
                'role': 'superuser',
                'permissions': 'all'
            },
            {
                'username': 'bursary_manager',
                'email': 'manager@westpokot.go.ke',
                'password': 'Manager@2024!',
                'first_name': 'Bursary',
                'last_name': 'Manager',
                'role': 'manager',
                'permissions': ['review', 'approve', 'reject', 'verify', 'analytics']
            },
            {
                'username': 'verification_officer',
                'email': 'verification@westpokot.go.ke',
                'password': 'Verify@2024!',
                'first_name': 'Verification',
                'last_name': 'Officer',
                'role': 'verifier',
                'permissions': ['review', 'verify', 'flag']
            },
            {
                'username': 'reviewer1',
                'email': 'reviewer1@westpokot.go.ke',
                'password': 'Review@2024!',
                'first_name': 'Application',
                'last_name': 'Reviewer',
                'role': 'reviewer',
                'permissions': ['review', 'analytics']
            },
            {
                'username': 'data_clerk',
                'email': 'clerk@westpokot.go.ke',
                'password': 'Clerk@2024!',
                'first_name': 'Data',
                'last_name': 'Clerk',
                'role': 'clerk',
                'permissions': ['view']
            }
        ]

        with transaction.atomic():
            # Create or get permission groups
            groups = self._create_permission_groups()

            for account in admin_accounts:
                try:
                    # Check if user exists
                    if reset and User.objects.filter(username=account['username']).exists():
                        User.objects.filter(username=account['username']).delete()
                        self.stdout.write(
                            self.style.WARNING(f"Deleted existing user: {account['username']}")
                        )

                    # Create user
                    if account['role'] == 'superuser':
                        user = User.objects.create_superuser(
                            username=account['username'],
                            email=account['email'],
                            password=account['password'],
                            first_name=account['first_name'],
                            last_name=account['last_name']
                        )
                    else:
                        user = User.objects.create_user(
                            username=account['username'],
                            email=account['email'],
                            password=account['password'],
                            first_name=account['first_name'],
                            last_name=account['last_name']
                        )
                        user.is_staff = True
                        user.save()

                    # Assign permissions based on role
                    if account['permissions'] != 'all':
                        group_name = account['role'].capitalize()
                        if group_name in groups:
                            user.groups.add(groups[group_name])

                    self.stdout.write(
                        self.style.SUCCESS(
                            f"✓ Created {account['role']}: {account['username']} "
                            f"(Password: {account['password']})"
                        )
                    )

                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"✗ Error creating {account['username']}: {str(e)}")
                    )

        # Display summary
        self._display_summary(admin_accounts)

    def _create_permission_groups(self):
        """Create permission groups with specific permissions"""
        content_type = ContentType.objects.get_for_model(BursaryApplication)
        
        # Define groups and their permissions
        group_permissions = {
            'Manager': [
                'view_bursaryapplication',
                'add_bursaryapplication',
                'change_bursaryapplication',
                'review_application',
                'approve_application',
                'reject_application',
                'view_analytics'
            ],
            'Verifier': [
                'view_bursaryapplication',
                'change_bursaryapplication',
                'review_application'
            ],
            'Reviewer': [
                'view_bursaryapplication',
                'review_application',
                'view_analytics'
            ],
            'Clerk': [
                'view_bursaryapplication'
            ]
        }

        groups = {}
        for group_name, perm_codenames in group_permissions.items():
            group, created = Group.objects.get_or_create(name=group_name)
            
            if created or True:  # Always update permissions
                group.permissions.clear()
                for codename in perm_codenames:
                    try:
                        # Try to get custom permission
                        perm = Permission.objects.get(
                            codename=codename,
                            content_type=content_type
                        )
                        group.permissions.add(perm)
                    except Permission.DoesNotExist:
                        # Try to get default permission
                        try:
                            perm = Permission.objects.get(codename=codename)
                            group.permissions.add(perm)
                        except Permission.DoesNotExist:
                            self.stdout.write(
                                self.style.WARNING(f"Permission not found: {codename}")
                            )
            
            groups[group_name] = group
            action = 'Created' if created else 'Updated'
            self.stdout.write(
                self.style.SUCCESS(f"{action} group: {group_name}")
            )

        return groups

    def _display_summary(self, accounts):
        """Display summary of created accounts"""
        self.stdout.write('\n' + '=' * 80)
        self.stdout.write(self.style.SUCCESS('ADMIN ACCOUNTS CREATED SUCCESSFULLY'))
        self.stdout.write('=' * 80 + '\n')
        
        self.stdout.write(self.style.WARNING('SAVE THESE CREDENTIALS SECURELY!\n'))
        
        for account in accounts:
            self.stdout.write(f"\n{account['role'].upper()}:")
            self.stdout.write(f"  Username: {account['username']}")
            self.stdout.write(f"  Password: {account['password']}")
            self.stdout.write(f"  Email: {account['email']}")
            self.stdout.write(f"  Access Level: {', '.join(account['permissions']) if isinstance(account['permissions'], list) else 'Full Access'}")
        
        self.stdout.write('\n' + '=' * 80)
        self.stdout.write(self.style.WARNING('\nRECOMMENDATIONS:'))
        self.stdout.write('  1. Change all passwords immediately after first login')
        self.stdout.write('  2. Enable two-factor authentication for superuser')
        self.stdout.write('  3. Store credentials in a secure password manager')
        self.stdout.write('  4. Regularly audit user access and permissions')
        self.stdout.write('=' * 80 + '\n')
        
        self.stdout.write(self.style.SUCCESS('\nAccess the admin panel at: /admin/'))