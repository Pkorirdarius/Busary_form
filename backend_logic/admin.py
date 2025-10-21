from django.contrib import admin
from .models import UserProfile, BursaryApplication, Document
# Register your models here.
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'id_number', 'phone', 'ward', 'location')
    search_fields = ('user__username', 'id_number', 'ward')


class DocumentInline(admin.TabularInline):
    model = Document
    extra = 0


@admin.register(BursaryApplication)
class BursaryAdmin(admin.ModelAdmin):
    list_display = ('user', 'institution_name', 'amount_requested', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username', 'institution_name')
    inlines = [DocumentInline]
    actions = ['approve_applications', 'reject_applications']

    def approve_applications(self, request, queryset):
        queryset.update(status="Approved")
    approve_applications.short_description = "Mark selected as Approved"

    def reject_applications(self, request, queryset):
        queryset.update(status="Rejected")
    reject_applications.short_description = "Mark selected as Rejected"
