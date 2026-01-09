"""
Utility functions for user roles and permissions
"""
from django.contrib.auth.models import Group


class UserRoleManager:
    """
    Centralized class for managing user roles and permissions
    """
    
    @staticmethod
    def get_user_role(user):
        """
        Get the primary role of a user
        Returns: 'admin', 'manager', 'staff', or None
        """
        if not user.is_authenticated:
            return None
        
        if user.is_superuser:
            return 'admin'
        
        if user.groups.filter(name='Manager').exists():
            return 'manager'
        
        if user.groups.filter(name='Staff').exists():
            return 'staff'
        
        return None
    
    @staticmethod
    def get_user_roles(user):
        """
        Get all roles of a user (in case of multiple group memberships)
        Returns: list of roles
        """
        if not user.is_authenticated:
            return []
        
        roles = []
        
        if user.is_superuser:
            roles.append('admin')
        
        user_groups = user.groups.values_list('name', flat=True)
        
        if 'Manager' in user_groups:
            roles.append('manager')
        
        if 'Staff' in user_groups:
            roles.append('staff')
        
        return roles
    
    @staticmethod
    def is_admin(user):
        """Check if user is admin"""
        return user.is_authenticated and user.is_superuser
    
    @staticmethod
    def is_manager(user):
        """Check if user is manager"""
        return (user.is_authenticated and 
                user.groups.filter(name='Manager').exists())
    
    @staticmethod
    def is_staff(user):
        """Check if user is staff"""
        return (user.is_authenticated and 
                user.groups.filter(name='Staff').exists())
    
    @staticmethod
    def is_manager_or_admin(user):
        """Check if user is manager or admin"""
        return (UserRoleManager.is_admin(user) or 
                UserRoleManager.is_manager(user))
    
    @staticmethod
    def is_staff_or_above(user):
        """Check if user is staff, manager, or admin"""
        return (UserRoleManager.is_admin(user) or 
                UserRoleManager.is_manager(user) or 
                UserRoleManager.is_staff(user))
    
    @staticmethod
    def is_approved(user):
        """Check if user is approved to access the system"""
        if not user.is_authenticated:
            return False
        
        # Superusers are always approved
        if user.is_superuser:
            return True
        
        # Check if user has profile and is approved
        if hasattr(user, 'userprofile'):
            return user.userprofile.is_approved
        
        return False
    
    @staticmethod
    def get_role_display_name(role):
        """Get display name for role"""
        role_names = {
            'admin': 'Administrator',
            'manager': 'Manager',
            'staff': 'Staff Member'
        }
        return role_names.get(role, 'Unknown')
    
    @staticmethod
    def get_role_permissions(role):
        """Get permissions description for role"""
        permissions = {
            'admin': [
                'Full system access',
                'User management',
                'All inventory operations',
                'System administration'
            ],
            'manager': [
                'Add inventory items',
                'Edit inventory items',
                'View all inventory',
                'Manage stock levels'
            ],
            'staff': [
                'View inventory items',
                'Search and filter items',
                'Check stock levels'
            ]
        }
        return permissions.get(role, [])
    
    @staticmethod
    def assign_role(user, role):
        """Assign a role to a user"""
        # Remove existing roles first
        user.groups.clear()
        
        if role == 'manager':
            group, created = Group.objects.get_or_create(name='Manager')
            user.groups.add(group)
        elif role == 'staff':
            group, created = Group.objects.get_or_create(name='Staff')
            user.groups.add(group)
        # Admin role is handled by is_superuser flag
    
    @staticmethod
    def get_context_for_user(user):
        """Get role context for templates"""
        role = UserRoleManager.get_user_role(user)
        return {
            'user_role': role,
            'user_role_display': UserRoleManager.get_role_display_name(role),
            'is_admin': UserRoleManager.is_admin(user),
            'is_manager': UserRoleManager.is_manager(user),
            'is_staff': UserRoleManager.is_staff(user),
            'is_manager_or_admin': UserRoleManager.is_manager_or_admin(user),
            'is_staff_or_above': UserRoleManager.is_staff_or_above(user),
            'is_approved': UserRoleManager.is_approved(user),
            'role_permissions': UserRoleManager.get_role_permissions(role)
        }