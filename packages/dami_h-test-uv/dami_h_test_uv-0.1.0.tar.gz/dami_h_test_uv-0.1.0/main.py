import argparse
import time
from typing import Tuple, Optional


def _fib_pair(n: int) -> Tuple[int, int]:
    """返回 (F(n), F(n+1))，使用快速倍增法（递归，O(log n)）。"""
    if n == 0:
        return 0, 1
    a, b = _fib_pair(n >> 1)
    c = a * ((b << 1) - a)
    d = a * a + b * b
    if n & 1:
        return d, c + d
    else:
        return c, d


def fib(n: int) -> int:
    """返回第 n 个斐波那契数（0-based），支持任意大整数。"""
    if n < 0:
        raise ValueError("n must be non-negative")
    return _fib_pair(n)[0]


def fib_mod(n: int, mod: int) -> int:
    """返回 F(n) mod mod，避免大整数中间膨胀。"""
    if n < 0:
        raise ValueError("n must be non-negative")
    if mod <= 0:
        raise ValueError("mod must be positive")

    def pair_mod(k: int) -> Tuple[int, int]:
        if k == 0:
            return 0, 1
        a, b = pair_mod(k >> 1)
        c = (a * ((b << 1) - a)) % mod
        d = (a * a + b * b) % mod
        if k & 1:
            return d, (c + d) % mod
        else:
            return c, d

    return pair_mod(n)[0]


def main():
    parser = argparse.ArgumentParser(description="高效斐波那契计算（快速倍增法）")
    parser.add_argument("n", type=int, help="计算 F(n)，n >= 0（0-based）")
    parser.add_argument("-m", "--mod", type=int, default=None, help="如果提供，返回 F(n) mod m")
    args = parser.parse_args()

    start = time.perf_counter()
    if args.mod is None:
        result = fib(args.n)
    else:
        result = fib_mod(args.n, args.mod)
    elapsed = time.perf_counter() - start

    print(result)
    print(f"计算耗时: {elapsed:.6f}s")


if __name__ == "__main__":
    main()
