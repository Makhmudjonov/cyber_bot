# admin.py

from django.contrib import admin

from apps.component.models.team import Player, Team

class PlayerInline(admin.TabularInline):
    model = Player
    extra = 0

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ("name",)
    inlines = [PlayerInline]

admin.site.register(Player)
