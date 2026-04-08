from django.contrib import admin
from .models import RoundResult, RoundResultSession


@admin.register(RoundResultSession)
class RoundResultSessionAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_published', 'uploaded_at')
    list_filter = ('is_published',)
    search_fields = ('title',)


@admin.register(RoundResult)
class RoundResultAdmin(admin.ModelAdmin):
    list_display = ('id', 'full_name', 'school', 'total_score', 'total_pct', 'medal', 'status')
    list_display_links = ('id',)
    list_editable = ('full_name', 'school', 'status')
    list_filter = ('status', 'medal', 'session')
    search_fields = ('full_name', 'school')
    list_per_page = 50
