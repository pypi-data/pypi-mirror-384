# tinyai/plots.py
import matplotlib.pyplot as plt
from .models import Weight, Memory

def show_weights(memory: Memory | None = None):
    mem = memory or Memory.objects.order_by("-id").first()
    if not mem:
        print("Sem memória criada.")
        return
    ws = list(Weight.objects.filter(memory=mem).values_list("value", flat=True))
    if not ws:
        print("Sem pesos.")
        return
    plt.hist(list(map(float, ws)), bins=50)
    plt.title("Distribuição de Pesos do TinyAI")
    plt.xlabel("Valor do Peso")
    plt.ylabel("Frequência")
    plt.show()
