from django.db import models
import json


class Memory(models.Model):
    """Represents the whole AI memory state."""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # You can still dump full JSON for debugging / backup
    raw_json = models.JSONField(default=dict)

    def __str__(self):
        return f"Memory {self.id} ({self.created_at.date()})"


class MemoryItem(models.Model):
    """Each training pair: question, answer, vectors, error."""
    memory = models.ForeignKey(Memory, on_delete=models.CASCADE, related_name="items")
    input_text = models.TextField()
    answer_text = models.TextField()
    input_vec = models.JSONField(default=dict)   # {idx: value}
    target_vec = models.JSONField(default=dict)  # {idx: value}
    avg_error = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    context_tags = models.JSONField(default=list)
    emotional_charge = models.FloatField(default=0.0)
    embedding = models.JSONField(default=list, blank=True, null=True)


    def __str__(self):
        return f"{self.input_text[:40]} → {self.answer_text[:40]}"


class Weight(models.Model):
    """All learned weights for hashed buckets."""
    memory = models.ForeignKey(Memory, on_delete=models.CASCADE, related_name="weights")
    index = models.IntegerField()
    value = models.FloatField()

    class Meta:
        unique_together = ("memory", "index")

    def __str__(self):
        return f"{self.index}: {self.value:.4f}"


class MemoryLink(models.Model):
    source = models.ForeignKey(MemoryItem, on_delete=models.CASCADE, related_name="links_from")
    target = models.ForeignKey(MemoryItem, on_delete=models.CASCADE, related_name="links_to")
    relation = models.CharField(max_length=100)  # e.g. 'is a type of', 'is part of', 'causes', 'used for'
    confidence = models.FloatField(default=0.5)


class ActivityLog(models.Model):
    memory = models.ForeignKey(Memory, on_delete=models.CASCADE, related_name="activity_logs")
    step = models.IntegerField(default=0)
    role = models.CharField(max_length=10, choices=[("user", "User"), ("ai", "AI")])
    text = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["timestamp"]

    def __str__(self):
        return f"[{self.role}] Step {self.step}: {self.text[:40]}"
