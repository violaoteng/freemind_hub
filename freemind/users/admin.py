from django.contrib import admin
from .models import User, Profile, Therapist, AssignedTherapist, Specialization

class UserAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        """Ensure the user is active when saved through the admin panel"""
        obj.is_active = True
        obj.save(is_admin_save=True)

class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'gender', 'dob', 'county', 'language', 'preferred_gender', 'get_specializations')
    readonly_fields = ('specializations',)  

    def get_specializations(self, obj):
        """Display selected specializations in a readable format"""
        return ", ".join([specialization.name for specialization in obj.specializations.all()])
    
    get_specializations.short_description = "Selected Specializations"

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        """Ensure the admin only sees the specializations assigned to the user"""
        if db_field.name == "specializations":
            if request.resolver_match and request.resolver_match.kwargs:
                profile_id = request.resolver_match.kwargs.get("object_id")
                if profile_id:
                    profile = Profile.objects.get(id=profile_id)
                    kwargs["queryset"] = profile.specializations.all()
                else:
                    kwargs["queryset"] = Specialization.objects.none()
        return super().formfield_for_manytomany(db_field, request, **kwargs)

class TherapistAdmin(admin.ModelAdmin):
    filter_horizontal = ('specializations',)  # Makes selecting multiple specializations easier

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        """Ensure only available specializations can be selected"""
        if db_field.name == "specializations":
            kwargs["queryset"] = Specialization.objects.all()  # Admin selects from all specializations
        return super().formfield_for_manytomany(db_field, request, **kwargs)

# Register models
admin.site.register(User, UserAdmin)
admin.site.register(Profile, ProfileAdmin)
admin.site.register(AssignedTherapist)
admin.site.register(Therapist, TherapistAdmin)
admin.site.register(Specialization)
