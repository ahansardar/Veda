#include <stdio.h>
#include <string.h>
#include <stdbool.h>
#include <ctype.h>
#include <stdlib.h>

typedef enum
{
    TOKEN_EOF = 0,
    TOKEN_NEWLINE,
    TOKEN_IDENTIFIER,
    TOKEN_KEYWORD,
    TOKEN_NUMBER,
    TOKEN_STRING,
    TOKEN_LPAREN,
    TOKEN_RPAREN,
    TOKEN_COMMA,
    TOKEN_LBRACKET,
    TOKEN_RBRACKET,
    TOKEN_LBRACE,
    TOKEN_RBRACE,
    TOKEN_COLON,
    TOKEN_DOT,
    TOKEN_PLUS,
    TOKEN_MINUS,
    TOKEN_STAR,
    TOKEN_SLASH,
    TOKEN_PERCENT,
    TOKEN_EQUAL,
    TOKEN_EQUAL_EQUAL,
    TOKEN_BANG_EQUAL,
    TOKEN_GREATER,
    TOKEN_GREATER_EQUAL,
    TOKEN_LESS,
    TOKEN_LESS_EQUAL,
    TOKEN_ERROR
} TokenType;

typedef struct
{
    int type;
    int line;
    int column;
    int length;
    const char *start;
} LexResult;

typedef struct
{
    const char *start;
    const char *current;
    int line;
    int column;
} Scanner;

Scanner scanner;

void initScanner(const char *source)
{
    scanner.start = source;
    scanner.current = source;
    scanner.line = 1;
    scanner.column = 1;
}

bool isAtEnd()
{
    return *scanner.current == '\0';
}

char advance()
{
    scanner.current++;
    scanner.column++;
    return scanner.current[-1];
}

char peek()
{
    return *scanner.current;
}

char peekNext()
{
    if (isAtEnd())
        return '\0';
    return scanner.current[1];
}

bool match(char expected)
{
    if (isAtEnd() || *scanner.current != expected)
        return false;
    scanner.current++;
    scanner.column++;
    return true;
}

LexResult makeToken(TokenType type)
{
    LexResult res;
    res.type = (int)type;
    res.start = scanner.start;
    res.length = (int)(scanner.current - scanner.start);
    res.line = scanner.line;
    // Calculate start column of the token
    res.column = scanner.column - res.length;
    return res;
}

LexResult errorToken(const char *message)
{
    LexResult res;
    res.type = (int)TOKEN_ERROR;
    res.start = message;
    res.length = (int)strlen(message);
    res.line = scanner.line;
    res.column = scanner.column;
    return res;
}

void skipWhitespace()
{
    for (;;)
    {
        char c = peek();
        switch (c)
        {
        case ' ':
        case '\r':
        case '\t':
            advance();
            break;
        case '#':
            while (peek() != '\n' && !isAtEnd())
                advance();
            break;
        default:
            return;
        }
    }
}

TokenType identifierType()
{

    return TOKEN_IDENTIFIER;
}

LexResult string()
{
    bool is_triple = false;
    if (peek() == '"' && peekNext() == '"' && scanner.current[2] == '"')
    {
        is_triple = true;
        advance();
        advance();
        advance();
    }
    else
    {
        advance(); // Opening quote
    }

    while (!isAtEnd())
    {
        if (is_triple)
        {
            if (peek() == '"' && peekNext() == '"' && scanner.current[2] == '"')
            {
                advance();
                advance();
                advance();
                return makeToken(TOKEN_STRING);
            }
        }
        else
        {
            if (peek() == '"')
            {
                advance();
                return makeToken(TOKEN_STRING);
            }
            if (peek() == '\n')
                break;
        }

        if (peek() == '\n')
        {
            scanner.line++;
            scanner.column = 0;
        }
        advance();
    }
    return errorToken("Unterminated string.");
}

LexResult next_token()
{
    skipWhitespace();
    scanner.start = scanner.current;

    if (isAtEnd())
        return makeToken(TOKEN_EOF);

    char c = advance();
    if (isdigit(c))
    {
        while (isdigit(peek()))
            advance();
        if (peek() == '.' && isdigit(peekNext()))
        {
            advance();
            while (isdigit(peek()))
                advance();
        }
        return makeToken(TOKEN_NUMBER);
    }
    if (isalpha(c) || c == '_')
    {
        while (isalnum(peek()) || peek() == '_')
            advance();

        return makeToken(TOKEN_IDENTIFIER);
    }

    switch (c)
    {
    case '(':
        return makeToken(TOKEN_LPAREN);
    case ')':
        return makeToken(TOKEN_RPAREN);
    case '[':
        return makeToken(TOKEN_LBRACKET);
    case ']':
        return makeToken(TOKEN_RBRACKET);
    case '{':
        return makeToken(TOKEN_LBRACE);
    case '}':
        return makeToken(TOKEN_RBRACE);
    case ':':
        return makeToken(TOKEN_COLON);
    case ',':
        return makeToken(TOKEN_COMMA);
    case '.':
        return makeToken(TOKEN_DOT);
    case '+':
        return makeToken(TOKEN_PLUS);
    case '-':
        return makeToken(TOKEN_MINUS);
    case '*':
        return makeToken(TOKEN_STAR);
    case '/':
        return makeToken(TOKEN_SLASH);
    case '%':
        return makeToken(TOKEN_PERCENT);
    case '\n':
    {
        LexResult res = makeToken(TOKEN_NEWLINE);
        scanner.line++;
        scanner.column = 1;
        return res;
    }
    case '=':
        return makeToken(match('=') ? TOKEN_EQUAL_EQUAL : TOKEN_EQUAL);
    case '!':
        return match('=') ? makeToken(TOKEN_BANG_EQUAL) : errorToken("Expected = after !");
    case '<':
        return makeToken(match('=') ? TOKEN_LESS_EQUAL : TOKEN_LESS);
    case '>':
        return makeToken(match('=') ? TOKEN_GREATER_EQUAL : TOKEN_GREATER);
    case '"':
        return string();
    }
    return errorToken("Unexpected character.");
}