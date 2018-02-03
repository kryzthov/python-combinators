params = {
  (type)? field (= expr)?
}




LOG_OP ::= AND | OR
NUM_OP ::= '+' | '-' | '*' | '/' | '**'
OP  ::= LOG_OP | NUM_OP


expr ::=
      literal
    | expr OP expr
    | IF expr expr ELSE expr




record ::= '{' field* '}'

field ::= (type)? IDENT (= expr)?


Investment = {
  Date date
  double cost_basis
  double value
}


Params = {
  Params previous
  int age
  array<Investment> investments = []
}





let Fibo(n) = {
  result = if (n <= 1) 1 else Fibo(n-1).result + Fibo(n-2).result
}



rec {
  l = [1, 2, 3]
}


rec = {
    x = 1
    y = x + 1
    z = x + y
}



Sub = {
    y = x + 1
}


rec = {
    x = 1
    sub = Sub(x = x)
}


type FinancialYear = {
    year: int
    age: int
}


let NextFinancialYear(previous: FinancialYear): FinancialYear = {
    year = previous.year + 1
    age = previous.age + 1

}



main = {
  fibo(n) = {
    result = if n <= 1 then 1 else fibo(n - 1).result + fibo(n - 2).result
  }

  fa(n) = {
    result = if (n % 2) == 0 then fa(n-1) else fb(n-1)
  }

  fb(n) = {
    result = if (n % 2) == 1 then fb(n-1) else fa(n-1)
  }

  f5 = fibo(5).result,

  n = 10,
  fn = fibo(n).result,
}
