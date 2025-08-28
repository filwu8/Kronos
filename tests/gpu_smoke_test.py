import os
import sys


def main():
    try:
        import torch
    except Exception as e:
        print("[FAIL] Cannot import torch:", e)
        sys.exit(1)

    print("torch:", torch.__version__, "cuda:", getattr(torch.version, "cuda", None))

    if not torch.cuda.is_available():
        print("[FAIL] torch.cuda.is_available() is False")
        sys.exit(2)

    try:
        dev = torch.device("cuda:0")
        name = torch.cuda.get_device_name(dev)
        props = torch.cuda.get_device_properties(dev)
        print("GPU:", name, f"({props.total_memory / 1024**3:.1f} GB)")

        # tiny smoke test
        a = torch.zeros((1, 1), device=dev)
        b = torch.ones((1, 1), device=dev)
        c = a.matmul(b)
        print("matmul result:", c.item())
        print("[OK] CUDA smoke test passed")
        sys.exit(0)
    except Exception as e:
        print("[FAIL] CUDA smoke test error:", e)
        sys.exit(3)


if __name__ == "__main__":
    main()

