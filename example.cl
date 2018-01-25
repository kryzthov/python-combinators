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
