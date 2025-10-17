from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Memory, MemoryItem, Weight, MemoryLink,ActivityLog


@admin.register(Memory)
class MemoryAdmin(admin.ModelAdmin):
    list_display = ("id", "created_at", "updated_at")
    search_fields = ("id",)
    list_filter = ("created_at", "updated_at")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)


@admin.register(MemoryItem)
class MemoryItemAdmin(admin.ModelAdmin):
    list_display = ("id", "memory", "short_input", "short_answer", "avg_error", "created_at")
    search_fields = ("input_text", "answer_text")
    list_filter = ("created_at", "memory")
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)

    def short_input(self, obj):
        return obj.input_text[:50] + ("..." if len(obj.input_text) > 50 else "")
    short_input.short_description = "Input"

    def short_answer(self, obj):
        return obj.answer_text[:50] + ("..." if len(obj.answer_text) > 50 else "")
    short_answer.short_description = "Answer"


@admin.register(Weight)
class WeightAdmin(admin.ModelAdmin):
    list_display = ("id", "memory", "index", "value")
    search_fields = ("index",)
    list_filter = ("memory",)
    ordering = ("index",)


@admin.register(MemoryLink)
class MemoryLinkAdmin(admin.ModelAdmin):
    list_display = ("id", "source_display", "relation", "target_display", "confidence")
    list_filter = ("relation",)
    search_fields = (
        "source__input_text",
        "target__input_text",
        "relation",
    )
    ordering = ("-confidence",)

    def source_display(self, obj):
        """Display short text for the source MemoryItem."""
        return f"{obj.source.input_text[:60]}..." if obj.source.input_text else "—"
    source_display.short_description = "Source"

    def target_display(self, obj):
        """Display short text for the target MemoryItem."""
        return f"{obj.target.answer_text[:60]}..." if obj.target.answer_text else "—"
    target_display.short_description = "Target"


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ("id", "memory", "step", "role", "short_text", "timestamp")
    list_filter = ("role", "timestamp")
    search_fields = ("text", "memory__id")
    ordering = ("-timestamp",)
    readonly_fields = ("timestamp",)

    def short_text(self, obj):
        return (obj.text[:75] + "...") if len(obj.text) > 75 else obj.text
    short_text.short_description = "Text"