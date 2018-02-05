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


federal_tax_brackets = {
    brackets = [
        {rate=0.10,  base=0,        max=18650,    capital_gain_rate=0},
        {rate=0.15,  base=18650,    max=75900,    capital_gain_rate=0},
        {rate=0.25,  base=10452.50, max=153100,   capital_gain_rate=0.15},
        {rate=0.28,  base=29752.50, max=233350,   capital_gain_rate=0.15},
        {rate=0.33,  base=52222.50, max=416700,   capital_gain_rate=0.15},
        {rate=0.35,  base=112728,   max=470700,   capital_gain_rate=0.15},
        {rate=0.396, base=131628,   max=math.inf, capital_gain_rate=0.20},
    ]
}

rec {
  xs = [1, 2, 3]

  ys = {
    empty = len(xs) == 0
    result = if empty then [] else
  }
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
