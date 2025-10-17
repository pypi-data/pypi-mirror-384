import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from .tinyai import TinyAIMemory

@csrf_exempt
@require_POST
def learn_view(request):
    data = json.loads(request.body.decode("utf-8"))
    q = data.get("question")
    a = data.get("answer")
    if not q or not a:
        return JsonResponse({"error": "The 'question' and 'answer' fields are required."}, status=400)
    ai = TinyAIMemory()
    avg_err = ai.learn(q, a)
    return JsonResponse({"status": "ok", "avg_error": avg_err})

@csrf_exempt
@require_POST
def ask_view(request):
    data = json.loads(request.body.decode("utf-8"))
    q = data.get("question")
    if not q:
        return JsonResponse({"error": "The 'question' field is required.."}, status=400)
    ai = TinyAIMemory()
    ans, dist = ai.answer(q)
    return JsonResponse({"answer": ans, "distance": dist})

@csrf_exempt
@require_POST
def attend_view(request):
    data = json.loads(request.body.decode("utf-8"))
    q = data.get("question")
    top_k = int(data.get("top_k", 5))
    if not q:
        return JsonResponse({"error": "Campo 'question' é obrigatório."}, status=400)
    ai = TinyAIMemory()
    ans = ai.answer_with_attention(q, top_k=top_k)
    return JsonResponse({"answer": ans})

@csrf_exempt
@require_POST
def reflect_view(request):
    ai = TinyAIMemory()
    n = ai.reflect()
    return JsonResponse({"status": "ok", "improvements": n})


@csrf_exempt
def knowledge_view(request):
    """Return a sample of what the AI has learned."""
    from ai_core.models import MemoryItem, Weight

    # Get last memory
    from ai_core.models import Memory
    m = Memory.objects.last()

    # Basic stats
    total_items = MemoryItem.objects.filter(memory=m).count()
    total_weights = Weight.objects.filter(memory=m).count()

    # Get a few examples
    examples = list(
        MemoryItem.objects.filter(memory=m)
        .values("input_text", "answer_text", "avg_error")[:10]
    )

    # Optional: Get top-weighted connections
    top_weights = list(
        Weight.objects.filter(memory=m)
        .order_by("-value")
        .values("index", "value")[:10]
    )

    data = {
        "total_memory_items": total_items,
        "total_weights": total_weights,
        "examples": examples,
        "strongest_weights": top_weights,
    }

    return JsonResponse(data, safe=False)


@csrf_exempt
@require_POST
def compose_view(request):
    data = json.loads(request.body.decode("utf-8"))
    q = data.get("question")
    top_k = int(data.get("top_k", 5))
    if not q:
        return JsonResponse({"error": "Question is required"}, status=400)
    ai = TinyAIMemory()
    answer = ai.compose_message(q, top_k)
    return JsonResponse({"message": answer})


@csrf_exempt
@require_POST
def chain_reasoning_view(request):
    data = json.loads(request.body.decode("utf-8"))
    q = data.get("question")
    top_k = int(data.get("top_k", 5))
    if not q:
        return JsonResponse({"error": "Question is required"}, status=400)
    ai = TinyAIMemory()
    answer = ai.chain_reasoning(q, top_k)
    return JsonResponse({"message": answer})
