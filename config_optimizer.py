#!/usr/bin/env python3
"""
🔧 MANGA TRANSLATOR OPTIMIZER V3.0
==================================

Smart configuration optimizer for maximum translation performance.
Automatically detects system capabilities and optimizes settings.

Features:
- Intelligent API key rotation
- Performance-based method selection
- Memory usage optimization
- Batch size auto-tuning
- Real-time performance monitoring

Author: MangaTranslator Team Enhanced
Version: 3.0 - Ultra Optimized
"""

import json
import os
import psutil
import time
from datetime import datetime
from typing import Dict, List, Any, Optional


class MangaTranslatorOptimizer:
    """
    🚀 SIÊU TỐI ƯU HÓA TRANSLATOR
    Tự động điều chỉnh cấu hình để đạt hiệu suất tối đa
    """
    
    def __init__(self, config_file="translator_config.json"):
        self.config_file = config_file
        self.default_config = self._get_default_config()
        self.config = self._load_or_create_config()
        self.performance_history = []
        
    def _get_default_config(self) -> Dict[str, Any]:
        """Get optimal default configuration based on system specs"""
        
        # Detect system capabilities
        cpu_count = psutil.cpu_count()
        memory_gb = psutil.virtual_memory().total / (1024**3)
        
        return {
            "version": "3.0",
            "last_updated": datetime.now().isoformat(),
            
            # 🎯 PERFORMANCE SETTINGS
            "performance": {
                "batch_size_auto": True,
                "optimal_batch_size": self._calculate_optimal_batch_size(cpu_count, memory_gb),
                "cache_enabled": True,
                "cache_max_size": min(10000, int(memory_gb * 1000)),  # Based on available RAM
                "parallel_processing": cpu_count > 2,
                "max_workers": min(4, cpu_count),
                "timeout_seconds": 30,
                "retry_attempts": 3
            },
            
            # 🤖 AI METHOD OPTIMIZATION
            "ai_methods": {
                "primary_method": "gemini",
                "fallback_method": "deepinfra", 
                "emergency_fallback": "nllb",
                "method_selection": "smart",  # auto, smart, fixed
                "quality_threshold": 0.8,
                "speed_priority": False  # True for speed, False for quality
            },
            
            # 🔑 API KEY MANAGEMENT
            "api_management": {
                "rotation_enabled": True,
                "load_balancing": True,
                "failure_tolerance": 3,
                "rate_limit_respect": True,
                "key_health_check": True,
                "daily_limit_buffer": 0.1  # Reserve 10% for safety
            },
            
            # 📊 MONITORING & ANALYTICS
            "monitoring": {
                "performance_tracking": True,
                "real_time_feedback": True,
                "detailed_logging": True,
                "metrics_collection": True,
                "auto_optimization": True,
                "alert_thresholds": {
                    "speed_below_chars_per_sec": 20,
                    "cache_hit_rate_below": 40,
                    "error_rate_above": 0.1
                }
            },
            
            # 🎨 TRANSLATION QUALITY
            "quality": {
                "context_awareness": True,
                "smart_formality_detection": True,
                "emotion_preservation": True,
                "cultural_adaptation": True,
                "sfx_optimization": True,
                "bubble_fitting": True,
                "consistency_checking": True
            },
            
            # 🌐 LANGUAGE SPECIFIC
            "languages": {
                "japanese": {
                    "keigo_detection": True,
                    "honorific_mapping": True,
                    "manga_terminology": True
                },
                "chinese": {
                    "classical_terms": True,
                    "hierarchy_respect": True,
                    "martial_arts_terms": True
                },
                "korean": {
                    "formality_levels": True,
                    "relationship_mapping": True,
                    "modern_expressions": True
                }
            }
        }
    
    def _calculate_optimal_batch_size(self, cpu_count: int, memory_gb: float) -> int:
        """Calculate optimal batch size based on system resources"""
        base_size = 5  # Conservative base
        
        # CPU factor
        cpu_factor = min(2.0, cpu_count / 4)
        
        # Memory factor  
        memory_factor = min(2.0, memory_gb / 8)
        
        # Combined optimal size
        optimal_size = int(base_size * cpu_factor * memory_factor)
        
        # Reasonable bounds
        return max(3, min(25, optimal_size))
    
    def _load_or_create_config(self) -> Dict[str, Any]:
        """Load existing config or create new optimized one"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # Merge with defaults for new features
                config = self._merge_configs(self.default_config, config)
                return config
                
            except Exception as e:
                print(f"⚠️ Error loading config: {e}")
                print("🔧 Creating new optimized config...")
        
        # Create new config
        self._save_config(self.default_config)
        return self.default_config.copy()
    
    def _merge_configs(self, default: Dict, existing: Dict) -> Dict:
        """Intelligently merge default and existing configs"""
        result = default.copy()
        
        for key, value in existing.items():
            if key in result:
                if isinstance(value, dict) and isinstance(result[key], dict):
                    result[key] = self._merge_configs(result[key], value)
                else:
                    result[key] = value
            else:
                result[key] = value
        
        return result
    
    def _save_config(self, config: Dict[str, Any]):
        """Save configuration to file"""
        config["last_updated"] = datetime.now().isoformat()
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            print(f"✅ Configuration saved to {self.config_file}")
        except Exception as e:
            print(f"❌ Error saving config: {e}")
    
    def get_optimal_settings(self, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        🎯 GET OPTIMAL SETTINGS
        Return optimized settings based on current context and performance history
        """
        settings = {
            "batch_size": self._get_optimal_batch_size(context),
            "method": self._get_optimal_method(context),
            "timeout": self._get_optimal_timeout(context),
            "cache_strategy": self._get_cache_strategy(context),
            "quality_mode": self._get_quality_mode(context)
        }
        
        return settings
    
    def _get_optimal_batch_size(self, context: Optional[Dict] = None) -> int:
        """Determine optimal batch size for current context"""
        base_size = self.config["performance"]["optimal_batch_size"]
        
        if not context:
            return base_size
        
        # Adjust based on text complexity
        text_count = context.get("text_count", 1)
        avg_length = context.get("avg_text_length", 20)
        
        # For very long texts, reduce batch size
        if avg_length > 100:
            return max(2, base_size // 2)
        
        # For many short texts, can increase batch size
        if avg_length < 20 and text_count > 10:
            return min(30, base_size * 2)
        
        return base_size
    
    def _get_optimal_method(self, context: Optional[Dict] = None) -> str:
        """Select optimal translation method"""
        method_config = self.config["ai_methods"]
        
        if method_config["method_selection"] == "fixed":
            return method_config["primary_method"]
        
        # Smart selection based on context and performance
        if context:
            source_lang = context.get("source_lang", "auto")
            quality_needed = context.get("quality_priority", True)
            speed_needed = context.get("speed_priority", False)
            
            # High quality contexts
            if quality_needed and not speed_needed:
                return "gemini"
            
            # Speed priority contexts
            if speed_needed:
                return "deepinfra"
            
            # Language-specific optimization
            if source_lang == "ja":
                return "gemini"  # Best for Japanese
            elif source_lang in ["zh", "ko"]:
                return "deepinfra"  # Good for Chinese/Korean
        
        return method_config["primary_method"]
    
    def _get_optimal_timeout(self, context: Optional[Dict] = None) -> int:
        """Calculate optimal timeout based on context"""
        base_timeout = self.config["performance"]["timeout_seconds"]
        
        if context:
            batch_size = context.get("batch_size", 1)
            # Increase timeout for larger batches
            return min(60, base_timeout + (batch_size // 5) * 5)
        
        return base_timeout
    
    def _get_cache_strategy(self, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Determine optimal cache strategy"""
        return {
            "enabled": self.config["performance"]["cache_enabled"],
            "max_size": self.config["performance"]["cache_max_size"],
            "preload_common": True,
            "context_aware": self.config["quality"]["context_awareness"]
        }
    
    def _get_quality_mode(self, context: Optional[Dict] = None) -> str:
        """Determine quality mode based on context"""
        if context:
            if context.get("batch_size", 1) > 20:
                return "batch_optimized"
            elif context.get("quality_priority", True):
                return "maximum_quality"
            elif context.get("speed_priority", False):
                return "speed_optimized"
        
        return "balanced"
    
    def record_performance(self, metrics: Dict[str, Any]):
        """Record performance metrics for optimization"""
        metrics["timestamp"] = datetime.now().isoformat()
        self.performance_history.append(metrics)
        
        # Keep only recent history (last 100 records)
        if len(self.performance_history) > 100:
            self.performance_history = self.performance_history[-100:]
        
        # Auto-optimize if enabled
        if self.config["monitoring"]["auto_optimization"]:
            self._auto_optimize_settings()
    
    def _auto_optimize_settings(self):
        """Automatically optimize settings based on performance history"""
        if len(self.performance_history) < 10:
            return  # Need enough data
        
        recent_metrics = self.performance_history[-10:]
        
        # Analyze batch size performance
        self._optimize_batch_size(recent_metrics)
        
        # Analyze method performance
        self._optimize_method_selection(recent_metrics)
        
        # Save optimized config
        self._save_config(self.config)
    
    def _optimize_batch_size(self, metrics: List[Dict]):
        """Optimize batch size based on performance"""
        batch_performances = {}
        
        for metric in metrics:
            batch_size = metric.get("batch_size", 1)
            efficiency = metric.get("efficiency_score", 50)
            
            if batch_size not in batch_performances:
                batch_performances[batch_size] = []
            batch_performances[batch_size].append(efficiency)
        
        # Find best performing batch size
        best_size = None
        best_avg_efficiency = 0
        
        for size, efficiencies in batch_performances.items():
            if len(efficiencies) >= 3:  # Need enough samples
                avg_efficiency = sum(efficiencies) / len(efficiencies)
                if avg_efficiency > best_avg_efficiency:
                    best_avg_efficiency = avg_efficiency
                    best_size = size
        
        if best_size and best_size != self.config["performance"]["optimal_batch_size"]:
            print(f"🎯 Auto-optimizing batch size: {self.config['performance']['optimal_batch_size']} → {best_size}")
            self.config["performance"]["optimal_batch_size"] = best_size
    
    def _optimize_method_selection(self, metrics: List[Dict]):
        """Optimize method selection based on performance"""
        method_performances = {}
        
        for metric in metrics:
            method = metric.get("method", "unknown")
            speed = metric.get("texts_per_second", 0)
            quality = metric.get("quality_score", 0.5)
            
            if method not in method_performances:
                method_performances[method] = {"speeds": [], "qualities": []}
            
            method_performances[method]["speeds"].append(speed)
            method_performances[method]["qualities"].append(quality)
        
        # Determine best method
        best_method = None
        best_score = 0
        
        for method, data in method_performances.items():
            if len(data["speeds"]) >= 3:
                avg_speed = sum(data["speeds"]) / len(data["speeds"])
                avg_quality = sum(data["qualities"]) / len(data["qualities"])
                
                # Combined score (adjust weights as needed)
                score = avg_speed * 0.3 + avg_quality * 0.7
                
                if score > best_score:
                    best_score = score
                    best_method = method
        
        if best_method and best_method != self.config["ai_methods"]["primary_method"]:
            print(f"🎯 Auto-optimizing primary method: {self.config['ai_methods']['primary_method']} → {best_method}")
            self.config["ai_methods"]["primary_method"] = best_method
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        if not self.performance_history:
            return {"status": "No performance data available"}
        
        recent = self.performance_history[-20:] if len(self.performance_history) >= 20 else self.performance_history
        
        report = {
            "summary": {
                "total_records": len(self.performance_history),
                "analysis_period": len(recent),
                "avg_speed": sum(m.get("texts_per_second", 0) for m in recent) / len(recent),
                "avg_efficiency": sum(m.get("efficiency_score", 50) for m in recent) / len(recent)
            },
            "recommendations": self._generate_recommendations(recent),
            "optimal_settings": self.get_optimal_settings(),
            "system_health": self._check_system_health()
        }
        
        return report
    
    def _generate_recommendations(self, metrics: List[Dict]) -> List[str]:
        """Generate performance recommendations"""
        recommendations = []
        
        avg_speed = sum(m.get("texts_per_second", 0) for m in metrics) / len(metrics)
        avg_cache_rate = sum(m.get("cache_hit_rate", 0) for m in metrics) / len(metrics)
        
        if avg_speed < 1:
            recommendations.append("🐌 Consider using batch processing to improve speed")
        
        if avg_cache_rate < 50:
            recommendations.append("💾 Cache hit rate is low - enable pre-caching of common phrases")
        
        if any(m.get("error_rate", 0) > 0.1 for m in metrics):
            recommendations.append("🔧 High error rate detected - check API key health")
        
        return recommendations
    
    def _check_system_health(self) -> Dict[str, Any]:
        """Check overall system health"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory_percent = psutil.virtual_memory().percent
        
        return {
            "cpu_usage": cpu_percent,
            "memory_usage": memory_percent,
            "health_status": "good" if cpu_percent < 80 and memory_percent < 80 else "warning",
            "recommendations": [
                "System resources are optimal" if cpu_percent < 50 and memory_percent < 50
                else "Consider reducing batch size if system feels slow"
            ]
        }


# Global optimizer instance
_optimizer_instance = None

def get_optimizer() -> MangaTranslatorOptimizer:
    """Get global optimizer instance"""
    global _optimizer_instance
    if _optimizer_instance is None:
        _optimizer_instance = MangaTranslatorOptimizer()
    return _optimizer_instance


if __name__ == "__main__":
    # Demo the optimizer
    optimizer = MangaTranslatorOptimizer()
    
    print("🚀 MangaTranslator Optimizer V3.0")
    print("=" * 50)
    
    # Show optimal settings
    settings = optimizer.get_optimal_settings()
    print("📊 OPTIMAL SETTINGS:")
    for key, value in settings.items():
        print(f"  {key}: {value}")
    
    print("\n📈 PERFORMANCE REPORT:")
    report = optimizer.get_performance_report()
    print(json.dumps(report, indent=2, ensure_ascii=False))
