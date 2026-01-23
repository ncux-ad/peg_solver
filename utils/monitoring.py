"""
utils/monitoring.py

Мониторинг производительности - Фаза 7.5.
"""

import time
from typing import Dict, List, Any, Optional
from collections import defaultdict
from datetime import datetime

from .logging import get_logger


class PerformanceMonitor:
    """Монитор производительности."""
    
    def __init__(self):
        self.metrics: Dict[str, List[float]] = defaultdict(list)
        self.counters: Dict[str, int] = defaultdict(int)
        self.timestamps: Dict[str, List[datetime]] = defaultdict(list)
        self.logger = get_logger()
    
    def record_time(self, operation: str, elapsed: float):
        """
        Записывает время выполнения операции.
        
        Args:
            operation: имя операции
            elapsed: время в секундах
        """
        self.metrics[operation].append(elapsed)
        self.timestamps[operation].append(datetime.now())
    
    def increment_counter(self, counter: str, value: int = 1):
        """
        Увеличивает счётчик.
        
        Args:
            counter: имя счётчика
            value: значение для увеличения
        """
        self.counters[counter] += value
    
    def get_stats(self, operation: Optional[str] = None) -> Dict[str, Any]:
        """
        Возвращает статистику.
        
        Args:
            operation: имя операции (если None, возвращает общую статистику)
            
        Returns:
            Словарь со статистикой
        """
        if operation:
            if operation not in self.metrics:
                return {}
            
            times = self.metrics[operation]
            return {
                'operation': operation,
                'count': len(times),
                'total': sum(times),
                'average': sum(times) / len(times) if times else 0.0,
                'min': min(times) if times else 0.0,
                'max': max(times) if times else 0.0,
                'last': times[-1] if times else 0.0
            }
        else:
            # Общая статистика
            stats = {
                'operations': {},
                'counters': dict(self.counters),
                'total_operations': sum(len(times) for times in self.metrics.values())
            }
            
            for op in self.metrics:
                stats['operations'][op] = self.get_stats(op)
            
            return stats
    
    def print_stats(self, operation: Optional[str] = None):
        """Выводит статистику в консоль."""
        stats = self.get_stats(operation)
        
        if operation:
            print(f"\nСтатистика операции '{operation}':")
            print(f"  Количество: {stats['count']}")
            print(f"  Общее время: {stats['total']:.3f}s")
            print(f"  Среднее время: {stats['average']:.3f}s")
            print(f"  Минимум: {stats['min']:.3f}s")
            print(f"  Максимум: {stats['max']:.3f}s")
        else:
            print("\nОбщая статистика:")
            print(f"  Всего операций: {stats['total_operations']}")
            print(f"\nОперации:")
            for op, op_stats in stats['operations'].items():
                print(f"  {op}: {op_stats['count']} раз, "
                      f"среднее {op_stats['average']:.3f}s")
            print(f"\nСчётчики:")
            for counter, value in stats['counters'].items():
                print(f"  {counter}: {value}")
    
    def reset(self):
        """Сбрасывает все метрики."""
        self.metrics.clear()
        self.counters.clear()
        self.timestamps.clear()


# Глобальный монитор
_monitor: Optional[PerformanceMonitor] = None


def get_monitor() -> PerformanceMonitor:
    """Возвращает глобальный монитор."""
    global _monitor
    if _monitor is None:
        _monitor = PerformanceMonitor()
    return _monitor


def monitor_time(operation: str):
    """
    Декоратор для мониторинга времени выполнения.
    
    Usage:
        @monitor_time('my_function')
        def my_function():
            ...
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            monitor = get_monitor()
            start = time.time()
            try:
                result = func(*args, **kwargs)
                elapsed = time.time() - start
                monitor.record_time(operation, elapsed)
                return result
            except Exception as e:
                elapsed = time.time() - start
                monitor.record_time(f"{operation}_error", elapsed)
                raise
        return wrapper
    return decorator
