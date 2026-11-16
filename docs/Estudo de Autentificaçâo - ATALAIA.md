# Este documento contém conteúdos relacionados a autenticação e proteção de sites.

# 

# 

# Como será feita a proteção da senha do usuário?

  

**Servidores nunca devem conhecer a verdadeira senha dos usuários**. Se o banco de dados vazar, os hackers não podem ter acesso às senhas. Por isso o método de proteção de senha utilizado é o **Hashing** que não é uma criptografia. O Hashing é um algoritmo que comprime as senhas de um modo que não pode ser revertido, é matematicamente impossível. O formulário HTML não tem poder para proteger os dados no ar. Se o site usar apenas HTTP (sem o "S" de *Secure*), a senha viaja em texto puro.

# E quando tiver senha duplicada?

Caso exista dois usuários com senhas idênticas, o hash para as duas será exatamente igual, por isso hackers usam Rainbow Tables para quebrar senhas comuns.

Para resolver isso, utilizamos o método de Salting: o salt gera um texto aleatório colado diretamente na senha antes de gerar o hash (ex: 123456 \+ x8f9a2). Assim, salvando a senha no banco de dados com o hash \+ salt.

# Como resolver o problema de inserção de senha toda vez que o usuário entra em uma nova página no site? 

Para resolver essa “amnésia” que se dá no HTTP, o servidor cria um espaço na memória, podendo ser ou em um banco ou rápido como no Redis. Funciona assim: “O usuário Joao acabou de logar”, o servidor olha para essa informação e gera um identificador único (Session ID), longo e aleatório. O python olha para esta informação e envia uma instrução HTTP exigindo que o navegador guarde o Session ID em um cookie.

Agora, toda vez que HTML pedir uma nova página, o navegador anexa esse Cookie com o ID. O python lê o Cookie, verifica a memória, reconhece o ID e identifica o usuário.

# Segurança de Cookies: 

Os Cookies gerados contêm dados sensíveis que podem ser roubados, Por isso é importante que se proteja também os Cookies. 

Para proteger os Cookies, o python precisa ser configurado com regras restritas. Primeiro usando o HttpOnly que impede que os códigos JavaScript (CSS e JS) leiam o Cookie, neutralizando ataques onde hackers injetem um script malicioso no HTML, ataques XSS, para roubar a sessão do usuário.

## Atributos do HttpOnly: 

* **HttpOnly**: Impede o acesso do JavaScript ao cookie.  
* **Seguro**: Garante que o cookie seja enviado apenas via HTTPS.  
* **Caminho=/**: Restringe o cookie a um caminho específico.  
* **SameSite=Strict**: Impede que o cookie seja enviado com requisições entre sites, mitigando ataques CSRF. 

## Como é na web.config: 

Adicione a seguinte configuração na seção \<system.web\>:

\<httpCookies httpOnlyCookies="true" requireSSL="true" /\>

* **httpOnlyCookies="true"**: Ativa o HttpOnly para todos os cookies.  
* **requireSSL="true"**: Garante que cookies sejam enviados apenas via HTTPS.

## Pragmática, como configurar o HttpOnly na aplicação: 

Crie um novo cookie HttpOnly  
HttpCookie meuHttpHttpOnlyCookie \= novo HttpCookie("SessionId", "abc123");  
myHttpOnlyCookie.HttpOnly \= true; Marque como HttpOnly  
myHttpOnlyCookie.Secure \= true; Certifique-se de que seja enviado via HTTPS  
Response.AppendCookie(myHttpOnlyCookie);

Essa abordagem permite a aplicação seletiva do atributo HttpOnly a Cookies específicas. 

## Regra do Secure:

O Secure utilizado junto com o HttpOnly, diz ao navegador: *"Só envie este cookie se a conexão for HTTPS"*. Impede roubo de cookies em redes públicas. 

A Flag Secure instrui o navegador a só enviar o Cookie em conexões HTTPS. Sem ela, um Cookie de sessão pode vazar qualquer requisição HTTP, como um link http\://, um redirect mal configurado, uma rede wi-fi hostil capturando o tráfego em texto claro.

## Regra SameSite=Lax ou Strict: 

O SameSite impede que o Cookie seja enviado se a requisição vier de um site de terceiros. Protegendo contra ataques CSRF.

Ele utiliza três valores importantes: 

Strict: O Cookie nunca acompanha as requisições vindas de outro site. Efeito colateral: se o usuário chega ao app por um link externo, ele aparece deslogado na primeira navegação, porque o Cookie não viajou.

Lax: O Cookie acompanha navegações de topo (como clicar num link), mas não requisições disparadas em segundo plano por outro site (um POST via formulário escondido, uma imagem, um fetch cross-site). Cobre a maioria dos casos de CSRF sem quebrar a experiência.

None: O Cookie viaja em todo contexto cross-site. Necessário para fluxos legítimos entre domínios (SSO. iframe, certas integrações). None exige Secure, o navegador rejeita SameSIte=None sem Secure.

Caso o SameSite não seja declarado, os navegadores modernos assumem Lax, o que pode ajudar, mas confiar no default implícito é frágil: deixe explícito.

Como se defender de ataques e quais são mais comuns? 

Ao projetar seu sistema de autenticação, você deve presumir que ele sofrerá ataques.

1. **SQL Injection (Injeção de Banco de Dados):**  
   * *O ataque:* O hacker digita no campo de usuário um código de banco de dados (ex: `' OR '1'='1`). Se o Python colar isso direto no banco, o código do hacker altera a lógica e ele entra sem senha.  
   * *A defesa:* **Consultas parametrizadas (Prepared Statements)** ou ORMs (como SQLAlchemy no Flask/Django). O Python trata o que o usuário digita estritamente como texto, nunca como código executável.  
2. **XSS (Cross-Site Scripting):**  
   * *O ataque:* O invasor consegue colocar um código JavaScript dentro da sua página HTML (por exemplo, no campo de comentários de um blog). Quando você acessa, o código rouba seu cookie.  
   * *A defesa:* Usar a flag `HttpOnly` nos cookies e garantir que o framework Python escape automaticamente os caracteres perigosos no HTML (Jinja2 e Django fazem isso por padrão).  
3. **Brute Force (Força Bruta) e Credential Stuffing:**  
   * *O ataque:* Robôs testam milhares de combinações de usuário e senha por minuto.  
   * *A defesa:* **Rate Limiting**. O Python deve contar quantas vezes um IP errou a senha e bloqueá-lo após 5 tentativas por alguns minutos (ou exigir um reCAPTCHA).

# REFERÊNCIAS:

Estudo para segurança de Cookies: [Cookies Secure, HttpOnly e SameSite: o que são e por que faltam no seu site · Fracta](https://fracta.pro/blog/cookies-secure-httponly-samesite) 

Estudo sobre Redis: [O que é o Redis? \| IBM](https://www.ibm.com/br-pt/think/topics/redis) 

Estudo sobre HttpOnly: [Cabeçalho Set-Cookie \- HTTP \| MDN](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Set-Cookie) 

Outras fontes: Gemini.

