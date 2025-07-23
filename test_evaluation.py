#!/usr/bin/env python3
"""
测试评估系统
"""

from evaluation_system import SystemEvaluator

def test_evaluation():
    """测试评估系统"""
    try:
        print("=== 测试评估系统 ===")
        
        evaluator = SystemEvaluator()
        
        # 测试加载数据集
        print("1. 测试加载数据集...")
        test_count = evaluator.load_test_dataset()
        print(f"   ✅ 成功加载 {test_count} 篇测试文章")
        
        if test_count == 0:
            print("   ⚠️ 没有找到标注数据，请先使用标注中心标注一些文章")
            return
        
        # 测试系统运行
        print("2. 测试系统运行...")
        evaluator.run_system_on_test_data()
        print("   ✅ 系统运行完成")
        
        # 测试重要性指标计算
        print("3. 测试重要性指标计算...")
        importance_metrics = evaluator.calculate_importance_metrics()
        print(f"   ✅ Precision: {importance_metrics['precision']:.3f}")
        print(f"   ✅ Recall: {importance_metrics['recall']:.3f}")
        print(f"   ✅ F1 Score: {importance_metrics['f1_score']:.3f}")
        print(f"   ✅ Accuracy: {importance_metrics['accuracy']:.3f}")
        
        # 测试分类指标计算
        print("4. 测试分类指标计算...")
        classification_metrics = evaluator.calculate_classification_metrics()
        print(f"   ✅ 分类准确率: {classification_metrics['overall_accuracy']:.3f}")
        print(f"   ✅ 测试文章数: {classification_metrics['total_articles']}")
        
        print("\n=== 评估系统测试成功 ===")
        
    except Exception as e:
        print(f"❌ 评估系统测试失败: {e}")

if __name__ == "__main__":
    test_evaluation()