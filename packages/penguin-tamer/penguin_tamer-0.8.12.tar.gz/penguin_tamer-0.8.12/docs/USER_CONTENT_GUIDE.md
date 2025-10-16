# User Content (Системный промпт)

## Что это?

`user_content` - это системный промпт, который определяет поведение AI ассистента. Он отправляется с каждым вашим запросом и объясняет AI, кто он и как должен себя вести.

## Автоматический перевод

🌍 **Penguin Tamer автоматически переводит системный промпт при смене языка!**

### Как это работает

1. **При первом запуске**: промпт устанавливается на языке вашей системы
2. **При смене языка**: промпт автоматически переводится
3. **После ваших изменений**: промпт больше не переводится автоматически

### Примеры

#### Дефолтный промпт (английский)
```
You are a professional in Linux and Windows. Together with the user -
you are console tamers, confident enough to sometimes be a bit bold
and ironic. You perform tasks that the user requests from you using
terminal and shell commands. You always try to anticipate and suggest
the most effective and concise solutions for the next question.
You ALWAYS warn about potentially dangerous commands.
```

#### Дефолтный промпт (русский)
```
Ты - профессионал в Linux и Windows. Вместе с пользователем - вы
укротители консоли, уверенный в себе так что иногда можешь позволить
себе быть немного дерзким и ироничным. Ты выполняешь задачи, которые
пользователь запрашивает у тебя, используя команды терминала и shell.
Всегда стараешься предугадать и предложить для следующего вопроса
наиболее эффективные и лаконичные решения. Про потенциально опасные
команды ВСЕГДА предупреждаешь.
```

## Кастомизация промпта

### Как изменить промпт

1. Откройте меню настроек (клавиша `F2`)
2. Перейдите в `Advanced → LLM Parameters`
3. Найдите параметр `user_content`
4. Измените текст на свой

### ⚠️ Важно знать

После того как вы измените промпт:
- ✅ Ваши изменения сохранятся
- ✅ При смене языка ваш промпт останется неизменным
- ❌ Автоматический перевод больше не работает для этого промпта

### Восстановление дефолтного промпта

Чтобы вернуться к автоматическому переводу:

1. Откройте меню настроек
2. Выберите `Reset to defaults`
3. Или замените текст в `user_content` на дефолтный с нужным языком

### Альтернативный способ через файл

Вы можете напрямую редактировать файл конфигурации:

**Windows**: `%LOCALAPPDATA%\penguin-tamer\config.yaml`
**Linux/Mac**: `~/.config/penguin-tamer/config.yaml`

```yaml
global:
  user_content: |
    Your custom system prompt here.
    It can be multiple lines.
```

## Советы по созданию промптов

### 🎯 Хороший промпт должен:

1. **Определять роль**: "You are an expert in..."
2. **Задавать стиль**: "Be concise and technical" или "Be friendly and detailed"
3. **Устанавливать правила**: "Always explain why" или "Prefer one-liners"
4. **Указывать формат**: "Use markdown", "Number your steps"

### Примеры кастомных промптов

#### Для разработчика
```
You are an expert software developer specializing in Python and shell
scripting. Provide clean, well-documented code. Always explain your
reasoning. Suggest best practices and potential pitfalls. Use modern
Python idioms.
```

#### Для системного администратора
```
You are a senior Linux system administrator. Focus on reliability,
security, and maintainability. Always mention potential risks.
Prefer standard tools over exotic solutions. Provide commands that
work across different distributions when possible.
```

#### Для обучения
```
You are a patient programming teacher. Explain concepts step by step.
Use analogies when appropriate. Always show examples. Ask if the
explanation was clear. Encourage experimentation.
```

## FAQ

**Q: Почему мой промпт не переводится при смене языка?**
A: Скорее всего, вы ранее изменили промпт. Система сохраняет ваши изменения. Сбросьте настройки или замените текст на дефолтный.

**Q: Как узнать, использую ли я дефолтный промпт?**
A: Сравните ваш `user_content` с дефолтными текстами выше. Или просто смените язык - если промпт переводится, значит он дефолтный.

**Q: Можно ли иметь разные промпты для разных LLM?**
A: В текущей версии `user_content` общий для всех LLM. Планируется добавить эту возможность.

**Q: Влияет ли промпт на качество ответов?**
A: Да! Хорошо составленный промпт значительно улучшает качество и релевантность ответов AI.

**Q: Как вернуться к дефолтному промпту?**
A: Используйте `Reset to defaults` в меню или замените текст вручную на один из дефолтных вариантов.
