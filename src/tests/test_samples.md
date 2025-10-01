# Test Samples for Anonymization

## Arabic Sample Text
```
مرحباً، اسمي أحمد محمد وأعمل في شركة مايكروسوفت في الرياض. 
يمكنكم التواصل معي على البريد الإلكتروني ahmed.mohamed@microsoft.com 
أو على رقم الهاتف 966501234567. عمري 32 سنة وأسكن في حي الملز.
زميلتي فاطمة علي تعمل أيضاً في نفس الشركة، وعمرها 28 سنة.
رقم هويتي الوطنية هو 1234567890.
```

Expected entities:
- PERSON: أحمد محمد, فاطمة علي
- ORGANIZATION: مايكروسوفت  
- EMAIL: ahmed.mohamed@microsoft.com
- AGE: 32 سنة, 28 سنة

## French Sample Text
```
    Bonjour, je m'appelle Jean Dupont et je travaille chez Google France à Paris.
    Mon adresse email est jean.dupont@google.com et mon téléphone est 01 42 68 53 00.
    J'ai 35 ans et j'habite au 15 rue de la Paix, 75001 Paris.
    Ma collègue Marie Martin travaille aussi dans notre équipe, elle a 29 ans.
    Mon numéro de sécurité sociale est 1 85 03 75 001 234 56.
```

Expected entities:
- PERSON: Jean Dupont, Marie Martin
- ORGANIZATION: Google France
- EMAIL: jean.dupont@google.com  
- AGE: 35 ans, 29 ans

## English Sample Text (for comparison)
```
Hello, my name is John Smith and I work at Microsoft Corporation in Seattle.
You can reach me at john.smith@microsoft.com or call me at +1-206-555-0123.
I am 34 years old and live at 123 Main Street, Seattle, WA 98101.
My colleague Sarah Johnson also works here, she's 27 years old.
My social security number is 123-45-6789.
```

Expected entities:
- PERSON: John Smith, Sarah Johnson
- ORGANIZATION: Microsoft Corporation
- EMAIL: john.smith@microsoft.com
- AGE: 34 years old, 27 years old