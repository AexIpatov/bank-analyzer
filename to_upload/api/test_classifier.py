from parsers.finclassifier import FinClassifier

def test_classifier():
    print("="*60)
    print("🧪 ТЕСТИРОВАНИЕ КЛАССИФИКАТОРА")
    print("="*60)
    
    classifier = FinClassifier()
    
    # Тестовые описания из выписок
    test_descriptions = [
        "Money added from LUIZA ROMANOVA Rekins Nr. A14-41-02/26",
        "Komisijas maksa Комиссия за обслуживание счета. За 02/2026",
        "Транзакция по карте на сумму 25,00 EUR, списана Lovable LOVABLE.DEV",
        "Apmaksa par rēķinu NR.510261192199(PVN=28,06,1.2.10.5)",
        "FACEBK *FFE3QG9KL2",
        "Cars Taxi",
        "Salary and other Payments: SALARY AMOUNT TRANSFER",
        "Rent for February and utilities January"
    ]
    
    print("\n📝 Результаты классификации:")
    print("-" * 60)
    
    for desc in test_descriptions:
        article = classifier.classify_article(desc)
        direction, subdirection = classifier.classify_direction(desc)
        
        print(f"\nОписание: {desc[:80]}...")
        print(f"  Статья: {article}")
        print(f"  Направление: {direction}")
        print(f"  Субнаправление: {subdirection}")

if __name__ == "__main__":
    test_classifier()