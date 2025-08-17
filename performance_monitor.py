#!/usr/bin/env python3
"""
Performance Monitor for MangaTranslator
======================================

Monitors and logs performance metrics for the translation system.

Features:
- Translation speed tracking
- Cache hit rate monitoring  
- Method comparison statistics
- Memory usage tracking
- Performance recommendations

Author: MangaTranslator Team
Version: 1.0
"""

import time
import psutil
import json
from datetime import datetime
from typing import Dict, List, Any


class PerformanceMonitor:
    """Monitor and analyze translation performance"""
    
    def __init__(self):
        self.metrics = {
            'translation_times': [],
            'cache_stats': [],
            'method_performance': {},
            'memory_usage': [],
            'batch_performance': []
        }
        self.session_start = time.time()
    
    def start_translation_timer(self):
        """Start timing a translation operation"""
        return time.time()
    
    def end_translation_timer(self, start_time, method, text_length, cache_hit=False):
        """End timing and record translation performance"""
        end_time = time.time()
        duration = end_time - start_time
        
        metric = {
            'timestamp': datetime.now().isoformat(),
            'method': method,
            'duration': duration,
            'text_length': text_length,
            'cache_hit': cache_hit,
            'speed_chars_per_sec': text_length / duration if duration > 0 else 0
        }
        
        self.metrics['translation_times'].append(metric)
        
        # Update method performance stats
        if method not in self.metrics['method_performance']:
            self.metrics['method_performance'][method] = {
                'total_calls': 0,
                'total_time': 0,
                'avg_time': 0,
                'cache_hits': 0,
                'cache_misses': 0
            }
        
        stats = self.metrics['method_performance'][method]
        stats['total_calls'] += 1
        stats['total_time'] += duration
        stats['avg_time'] = stats['total_time'] / stats['total_calls']
        
        if cache_hit:
            stats['cache_hits'] += 1
        else:
            stats['cache_misses'] += 1
    
    def record_cache_stats(self, cache_size, total_requests, cache_hits):
        """Record cache performance statistics"""
        hit_rate = (cache_hits / total_requests * 100) if total_requests > 0 else 0
        
        self.metrics['cache_stats'].append({
            'timestamp': datetime.now().isoformat(),
            'cache_size': cache_size,
            'total_requests': total_requests,
            'cache_hits': cache_hits,
            'hit_rate': hit_rate
        })
    
    def record_memory_usage(self):
        """Record current memory usage"""
        process = psutil.Process()
        memory_info = process.memory_info()
        
        self.metrics['memory_usage'].append({
            'timestamp': datetime.now().isoformat(),
            'rss_mb': memory_info.rss / 1024 / 1024,  # Convert to MB
            'vms_mb': memory_info.vms / 1024 / 1024,
            'percent': process.memory_percent()
        })
    
    def record_batch_performance(self, batch_size, total_time, cache_hits):
        """
        🚀 ENHANCED BATCH PERFORMANCE TRACKING V3.0
        Record enhanced batch processing metrics with AI insights
        """
        batch_metric = {
            'timestamp': datetime.now().isoformat(),
            'batch_size': batch_size,
            'total_time': total_time,
            'avg_time_per_item': total_time / batch_size if batch_size > 0 else 0,
            'cache_hits': cache_hits,
            'cache_hit_rate': (cache_hits / batch_size * 100) if batch_size > 0 else 0,
            'texts_per_second': batch_size / total_time if total_time > 0 else 0,
            'efficiency_score': self._calculate_batch_efficiency(batch_size, total_time, cache_hits),
            'performance_grade': self._get_performance_grade(batch_size, total_time, cache_hits)
        }
        
        self.metrics['batch_performance'].append(batch_metric)
        
        # Real-time performance feedback
        if batch_size >= 10:  # For significant batches
            print(f"📊 BATCH METRICS: {batch_size} texts in {total_time:.2f}s")
            print(f"⚡ Speed: {batch_metric['texts_per_second']:.1f} texts/sec")
            print(f"💾 Cache hits: {cache_hits}/{batch_size} ({batch_metric['cache_hit_rate']:.1f}%)")
            print(f"🏆 Grade: {batch_metric['performance_grade']}")
    
    def _calculate_batch_efficiency(self, batch_size, duration, cache_hits):
        """Calculate batch efficiency score (0-100)"""
        # Base speed score (target: 2+ texts/sec)
        speed_score = min(100, (batch_size / duration) / 2 * 100) if duration > 0 else 0
        
        # Cache efficiency score
        cache_score = (cache_hits / batch_size * 100) if batch_size > 0 else 0
        
        # Batch size bonus (larger batches are more efficient)
        size_bonus = min(20, batch_size / 5)  # Up to 20 points for batch size
        
        return min(100, (speed_score * 0.5 + cache_score * 0.3 + size_bonus * 0.2))
    
    def _get_performance_grade(self, batch_size, duration, cache_hits):
        """Get performance grade based on metrics"""
        efficiency = self._calculate_batch_efficiency(batch_size, duration, cache_hits)
        
        if efficiency >= 90:
            return "🚀 EXCELLENT"
        elif efficiency >= 80:
            return "⭐ GREAT"
        elif efficiency >= 70:
            return "✅ GOOD"
        elif efficiency >= 60:
            return "🔶 AVERAGE"
        else:
            return "🔴 NEEDS_IMPROVEMENT"
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        summary = {
            'session_duration': time.time() - self.session_start,
            'total_translations': len(self.metrics['translation_times']),
            'method_stats': {},
            'cache_performance': {},
            'recommendations': []
        }
        
        # Method performance analysis
        for method, stats in self.metrics['method_performance'].items():
            summary['method_stats'][method] = {
                'avg_time': round(stats['avg_time'], 3),
                'total_calls': stats['total_calls'],
                'cache_hit_rate': round((stats['cache_hits'] / stats['total_calls'] * 100), 1) if stats['total_calls'] > 0 else 0
            }
        
        # Cache performance
        if self.metrics['cache_stats']:
            latest_cache = self.metrics['cache_stats'][-1]
            summary['cache_performance'] = {
                'current_size': latest_cache['cache_size'],
                'hit_rate': round(latest_cache['hit_rate'], 1),
                'total_requests': latest_cache['total_requests']
            }
        
        # Generate recommendations
        summary['recommendations'] = self._generate_recommendations()
        
        return summary
    
    def _generate_recommendations(self) -> List[str]:
        """Generate performance optimization recommendations"""
        recommendations = []
        
        # Cache analysis
        if self.metrics['cache_stats']:
            latest_cache = self.metrics['cache_stats'][-1]
            if latest_cache['hit_rate'] < 30:
                recommendations.append("Consider preloading common phrases to improve cache hit rate")
            elif latest_cache['hit_rate'] > 80:
                recommendations.append("Excellent cache performance! Translation speed is optimized")
        
        # Method performance analysis
        if self.metrics['method_performance']:
            # Find fastest method
            fastest_method = min(self.metrics['method_performance'].items(), 
                               key=lambda x: x[1]['avg_time'])
            if fastest_method[1]['avg_time'] > 2.0:
                recommendations.append("Consider using batch translation for multiple texts")
            
            # Check if Gemini is being used effectively
            if 'gemini' in self.metrics['method_performance']:
                gemini_stats = self.metrics['method_performance']['gemini']
                if gemini_stats['avg_time'] > 5.0:
                    recommendations.append("Gemini responses are slow - check network connection or consider fallback")
        
        # Memory usage analysis
        if self.metrics['memory_usage']:
            latest_memory = self.metrics['memory_usage'][-1]
            if latest_memory['percent'] > 80:
                recommendations.append("High memory usage detected - consider clearing cache periodically")
        
        # Batch performance analysis
        if self.metrics['batch_performance']:
            avg_batch_hit_rate = sum(b['cache_hit_rate'] for b in self.metrics['batch_performance']) / len(self.metrics['batch_performance'])
            if avg_batch_hit_rate < 50:
                recommendations.append("Low batch cache hit rate - consider pre-processing similar texts together")
        
        return recommendations
    
    def export_metrics(self, filename: str = None):
        """Export metrics to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"performance_metrics_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.metrics, f, indent=2, ensure_ascii=False)
        
        print(f"📊 Performance metrics exported to {filename}")
    
    def print_live_stats(self):
        """Print live performance statistics"""
        summary = self.get_performance_summary()
        
        print("\n" + "="*50)
        print("📊 LIVE PERFORMANCE STATS")
        print("="*50)
        
        print(f"Session Duration: {summary['session_duration']:.1f}s")
        print(f"Total Translations: {summary['total_translations']}")
        
        if summary['method_stats']:
            print("\nMethod Performance:")
            for method, stats in summary['method_stats'].items():
                print(f"  {method.upper()}: {stats['avg_time']:.3f}s avg, {stats['cache_hit_rate']:.1f}% cache hit")
        
        if summary['cache_performance']:
            cache = summary['cache_performance']
            print(f"\nCache: {cache['current_size']} entries, {cache['hit_rate']:.1f}% hit rate")
        
        if summary['recommendations']:
            print("\nRecommendations:")
            for rec in summary['recommendations']:
                print(f"  • {rec}")
        
        print("="*50)


# Global performance monitor instance
performance_monitor = PerformanceMonitor()
