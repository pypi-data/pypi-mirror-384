from dataclasses import dataclass
from string import ascii_lowercase


class ProofActionError(Exception):
    pass

class InferenceError(Exception):
    pass

class JustificationError(InferenceError):
    pass


@dataclass
class Metavar:
    domain_pred: object = None

    count = 0

    def __post_init__(self):
        type(self).count += 1
        self.id = type(self).count
        self.value = None

    def __str__(self):
        return f'?m{self.id}'

    def __eq__(self, value):
        # Check safety
        p = self.domain_pred
        if p and not p(value):
            return False
        if self.value is None:
            self.value = value
            return True
        return self.value == value


class Formula:

    def __str__(self):
        s = self._str()
        if s[0] == '(' and s[-1] == ')':
            return s[1:-1]
        return s

# TFL
@dataclass(frozen=True)
class Falsum(Formula):

    def _str(self):
        return '⊥'

@dataclass(frozen=True)
class PropVar(Formula):
    name: str

    def _str(self):
        return self.name

@dataclass(frozen=True)
class Not(Formula):
    inner: Formula

    def _str(self):
        return f'¬{self.inner._str()}'

@dataclass(frozen=True)
class And(Formula):
    left: Formula
    right: Formula

    def _str(self):
        return f'({self.left._str()} ∧ {self.right._str()})'

@dataclass(frozen=True)
class Or(Formula):
    left: Formula
    right: Formula

    def _str(self):
        return f'({self.left._str()} ∨ {self.right._str()})'

@dataclass(frozen=True)
class Imp(Formula):
    left: Formula
    right: Formula

    def _str(self):
        return f'({self.left._str()} → {self.right._str()})'

@dataclass(frozen=True)
class Iff(Formula):
    left: Formula
    right: Formula

    def _str(self):
        return f'({self.left._str()} ↔ {self.right._str()})'

# FOL
@dataclass(frozen=True)
class Term:
    name: str

    names = list(ascii_lowercase)

    def __str__(self):
        return self.name

class Const(Term):
    names = [t for t in Term.names if 'a' <= t <= 'r']

class Var(Term):
    names = [t for t in Term.names if 's' <= t <= 'z']

@dataclass(frozen=True)
class Pred(Formula):
    name: str
    args: tuple[Term]

    def _str(self):
        return self.name + ''.join(str(t) for t in self.args)

@dataclass(frozen=True)
class Eq(Formula):
    left: Term
    right: Term

    def _str(self):
        return f'{self.left} = {self.right}'

@dataclass(frozen=True)
class Forall(Formula):
    var: Var
    inner: Formula

    def _str(self):
        return f'∀{self.var}{self.inner._str()}'

@dataclass(frozen=True)
class Exists(Formula):
    var: Var
    inner: Formula

    def _str(self):
        return f'∃{self.var}{self.inner._str()}'

# ML
@dataclass(frozen=True)
class Box(Formula):
    inner: Formula

    def _str(self):
        return f'□{self.inner._str()}'

@dataclass(frozen=True)
class Dia(Formula):
    inner: Formula

    def _str(self):
        return f'♢{self.inner._str()}'

@dataclass(frozen=True)
class BoxMarker:

    def __str__(self):
        return '□'


@dataclass(frozen=True)
class Rule:
    name: str
    func: object

    def __str__(self):
        return self.name
    
    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)


@dataclass(frozen=True)
class Justification:
    rule: Rule
    citations: tuple

    def __str__(self):
        if not self.citations:
            return str(self.rule)

        j_list = []
        for idx in self.citations:
            if isinstance(idx, int):
                j_list.append(str(idx))
            else:
                i, j = idx
                j_list.append(f'{i}-{j}')
        return f"{self.rule}, {','.join(j_list)}"


class Rules:
    PR = Rule('PR', None)
    AS = Rule('AS', None)
    rules, strict = [], []

    @classmethod
    def add(cls, name, strict=False):
        def decorator(func):
            rule = Rule(name, func)
            cls.rules.append(rule)
            if strict:
                cls.strict.append(rule)
            return staticmethod(func)
        return decorator


def verify_arity(premises, n):
    if len(premises) != n:
        raise JustificationError('Invalid number of citations provided.')
    return premises if n != 1 else premises[0]


def assumption_constants(scope):
    a_rules = [Rules.PR, Rules.AS]
    a_constants = set()
    for obj in scope:
        if obj.is_line() and obj.justification.rule in a_rules:
            a_constants.update(constants(obj.formula))
    return a_constants


class TFL:
    
    @Rules.add('X')
    def X(premises, **kwargs):
        a = verify_arity(premises, 1)
        if not (a.is_line() and isinstance(a.formula, Falsum)):
            raise JustificationError('Invalid application of "X".')
        return [Metavar()]
    
    @Rules.add('¬I')
    def NotI(premises, **kwargs):
        a = verify_arity(premises, 1)
        if not (a.is_subproof() and isinstance(a.conclusion, Falsum)):
            raise JustificationError('Invalid application of "¬I".')
        return [Not(a.assumption)]
    
    @Rules.add('¬E')
    def NotE(premises, **kwargs):
        a, b = verify_arity(premises, 2)
        if not (a.is_line() and isinstance(a := a.formula, Not) 
                and b.is_line() and b.formula == a.inner):
            raise JustificationError('Invalid application of "¬E".')
        return [Falsum()]
    
    @Rules.add('∧I')
    def AndI(premises, **kwargs):
        a, b = verify_arity(premises, 2)
        if not (a.is_line() and b.is_line()):
            raise JustificationError('Invalid application of "∧I".')
        return [And(a.formula, b.formula)]
    
    @Rules.add('∧E')
    def AndE(premises, **kwargs):
        a = verify_arity(premises, 1)
        if not (a.is_line() and isinstance(a := a.formula, And)):
            raise JustificationError('Invalid application of "∧E".')
        return [a.left, a.right]
    
    @Rules.add('∨I')
    def OrI(premises, **kwargs):
        a = verify_arity(premises, 1)
        if not a.is_line():
            raise JustificationError('Invalid application of "∨I".')
        m1, m2 = Metavar(), Metavar()
        return [Or(a.formula, m1), Or(m2, a.formula)]

    @Rules.add('∨E')
    def OrE(premises, **kwargs):
        a, b, c = verify_arity(premises, 3)
        if not (a.is_line() and isinstance(a := a.formula, Or) 
                and b.is_subproof() and c.is_subproof()):
            raise JustificationError('Invalid application of "∨E".')
        
        ba, bc = b.assumption, b.conclusion
        ca, cc = c.assumption, c.conclusion
        if not ((a.left, a.right) in [(ba, ca), (ca, ba)] and bc == cc and bc):
            raise JustificationError('Invalid application of "∨E".')
        return [bc]
    
    @Rules.add('→I')
    def ImpI(premises, **kwargs):
        a = verify_arity(premises, 1)
        if not (a.is_subproof() and a.conclusion):
            raise JustificationError('Invalid application of "→I".')
        return [Imp(a.assumption, a.conclusion)]
    
    @Rules.add('→E')
    def ImpE(premises, **kwargs):
        a, b = verify_arity(premises, 2)
        if not (a.is_line() and isinstance(a := a.formula, Imp) 
                and b.is_line() and b.formula == a.left):
            raise JustificationError('Invalid application of "→E".')
        return [a.right]
    
    @Rules.add('↔I')
    def IffI(premises, **kwargs):
        a, b = verify_arity(premises, 2)
        if not (a.is_subproof() and b.is_subproof()):
            raise JustificationError('Invalid application of "↔I".')
        
        aa, ac = a.assumption, a.conclusion
        ba, bc = b.assumption, b.conclusion
        if not (aa == bc and ba == ac):
            raise JustificationError('Invalid application of "↔I".')
        return [Iff(aa, ac), Iff(ba, bc)]
    
    @Rules.add('↔E')
    def IffE(premises, **kwargs):
        a, b = verify_arity(premises, 2)
        if not (a.is_line() and isinstance(a := a.formula, Iff) and b.is_line()):
            raise JustificationError('Invalid application of "↔E".')
        
        if b.formula == a.left:
            return [a.right]
        if b.formula == a.right:
            return [a.left]
        raise JustificationError('Invalid application of "↔E".')
    
    @Rules.add('R')
    def R(premises, **kwargs):
        a = verify_arity(premises, 1)
        if not a.is_line():
            raise JustificationError('Invalid application of "R".')
        return [a.formula]
    
    @Rules.add('IP')
    def IP(premises, **kwargs):
        a = verify_arity(premises, 1)
        if not (a.is_subproof() and isinstance(a.assumption, Not) 
                and isinstance(a.conclusion, Falsum)):
            raise JustificationError('Invalid application of "IP".')
        return [a.assumption.inner]
    
    @Rules.add('DS')
    def DS(premises, **kwargs):
        a, b = verify_arity(premises, 2)
        if not (a.is_line() and isinstance(a := a.formula, Or) 
                and b.is_line() and isinstance(b := b.formula, Not)):
            raise JustificationError('Invalid application of "DS".')
        
        if b.inner == a.left:
            return [a.right]
        if b.inner == a.right:
            return [a.left]
        raise JustificationError('Invalid application of "DS".')

    @Rules.add('MT')
    def MT(premises, **kwargs):
        a, b = verify_arity(premises, 2)
        if not (a.is_line() and isinstance(a := a.formula, Imp) 
                and b.is_line() and isinstance(b := b.formula, Not) 
                and b.inner == a.right):
            raise JustificationError('Invalid application of "MT".')
        return [Not(a.left)]

    @Rules.add('DNE')
    def DNE(premises, **kwargs):
        a = verify_arity(premises, 1)
        if not (a.is_line() and isinstance(a := a.formula, Not) 
                and isinstance(a.inner, Not)):
            raise JustificationError('Invalid application of "DNE".')
        return [a.inner.inner]

    @Rules.add('LEM')
    def LEM(premises, **kwargs):
        a, b = verify_arity(premises, 2)
        if not (a.is_subproof() and b.is_subproof()):
            raise JustificationError('Invalid application of "LEM".')
        
        aa, ac = a.assumption, a.conclusion
        ba, bc = b.assumption, b.conclusion
        if not (((isinstance(aa, Not) and aa.inner == ba) 
                 or (isinstance(ba, Not) and ba.inner == aa)) 
                and ac == bc and ac):
            raise JustificationError('Invalid application of "LEM".')
        return [ac]

    @Rules.add('DeM')
    def DeM(premises, **kwargs):
        c = verify_arity(premises, 1)
        if not c.is_line():
            raise JustificationError('Invalid application of "DeM".')

        match c.formula:
            case Not(Or(a, b)):
                return [And(Not(a), Not(b))]
            case And(Not(a), Not(b)):
                return [Not(Or(a, b))]
            case Not(And(a, b)):
                return [Or(Not(a), Not(b))]
            case Or(Not(a), Not(b)):
                return [Not(And(a, b))]
        
        raise JustificationError('Invalid application of "DeM".')


class FOL(TFL):

    @Rules.add('=I')
    def EqI(premises, **kwargs):
        verify_arity(premises, 0)
        m = Metavar()
        return [Eq(m, m)]
    
    @Rules.add('=E')
    def EqE(premises, **kwargs):
        a, b = verify_arity(premises, 2)
        if not (a.is_line() and isinstance(a := a.formula, Eq) and b.is_line()):
            raise JustificationError('Invalid application of "=E".')
        terms = {a.left, a.right}
        def gen(): return Metavar(lambda obj: obj in terms)
        return [sub_terms(b.formula, terms, gen)]

    @Rules.add('∀I')
    def ForallI(premises, conclusion, scope, **kwargs):
        a = verify_arity(premises, 1)
        if not (a.is_line() and isinstance(conclusion, Forall)):
            raise JustificationError('Invalid application of "∀I".')
        var = conclusion.var
        def ignore(v): return v == var
        a_constants = assumption_constants(scope[0])

        schemes = [Forall(var, a.formula)]
        for c in constants(a.formula):
            if c in a_constants:
                continue
            inner = sub_terms(a.formula, {c}, lambda: var, ignore)
            schemes.append(Forall(var, inner))
        return schemes
    
    @Rules.add('∀E')
    def ForallE(premises, **kwargs):
        a = verify_arity(premises, 1)
        if not (a.is_line() and isinstance(a := a.formula, Forall)):
            raise JustificationError('Invalid application of "∀E".')
        m = Metavar()  # restrict to constants
        return [sub_terms(a.inner, {a.var}, lambda: m)]

    @Rules.add('∃I')
    def ExistsI(premises, conclusion, **kwargs):
        a = verify_arity(premises, 1)
        if not (a.is_line() and isinstance(conclusion, Exists)):
            raise JustificationError('Invalid application of "∃I".')
        var = conclusion.var
        def ignore(v): return v == var

        schemes = [Exists(var, a.formula)]
        for c in constants(a.formula):
            def gen(): return Metavar(lambda obj: obj in {c, var})
            inner = sub_terms(a.formula, {c}, gen, ignore)
            schemes.append(Exists(var, inner))
        return schemes
    
    @Rules.add('∃E')
    def ExistsE(premises, scope, **kwargs):
        a, b = verify_arity(premises, 2)
        if not (a.is_line() and isinstance(a := a.formula, Exists) 
                and b.is_subproof() and b.conclusion):
            raise JustificationError('Invalid application of "∃E".')
        m = Metavar()  # restrict to constants
        scheme = sub_terms(a.inner, {a.var}, lambda: m)
        if b.assumption != scheme:
            raise JustificationError('Invalid application of "∃E".')
        
        a_constants = assumption_constants(scope[0] + scope[1])
        a_constants.update(constants(a), constants(b.conclusion))
        if m.value in a_constants:
            raise JustificationError('Invalid application of "∃E".')
        return [b.conclusion]

    @Rules.add('CQ')
    def CQ(premises, **kwargs):
        a = verify_arity(premises, 1)
        if not a.is_line():
            raise JustificationError('Invalid application of "CQ".')

        match a.formula:
            case Forall(v, Not(b)):
                return [Not(Exists(v, b))]
            case Not(Exists(v, b)):
                return [Forall(v, Not(b))]
            case Exists(v, Not(b)):
                return [Not(Forall(v, b))]
            case Not(Forall(v, b)):
                return [Exists(v, Not(b))]
        
        raise JustificationError('Invalid application of "CQ".')


class MLK(TFL):

    @Rules.add('□I')
    def BoxI(premises, **kwargs):
        a = verify_arity(premises, 1)
        if not (a.is_subproof() and isinstance(a.assumption, BoxMarker) 
                and a.conclusion):
            raise JustificationError('Invalid application of "□I".')
        return [Box(a.conclusion)]
    
    @Rules.add('□E', strict=True)
    def BoxE(premises, scope, **kwargs):
        a = verify_arity(premises, 1)
        if not (a.is_line() and isinstance(a := a.formula, Box)):
            raise JustificationError('Invalid application of "□E".')
        
        lines = [obj.formula for obj in scope[1] if obj.is_line()]
        if lines.count(BoxMarker()) != 1:
            raise JustificationError('Invalid application of "□E".')
        return [a.inner]

    @Rules.add('Def♢')
    def DefDia(premises, **kwargs):
        a = verify_arity(premises, 1)
        if not a.is_line():
            raise JustificationError('Invalid application of "Def♢".')

        match a.formula:
            case Not(Box(Not(b))):
                return [Dia(b)]
            case Dia(b):
                return [Not(Box(Not(b)))]
        
        raise JustificationError('Invalid application of "Def♢".')

    @Rules.add('MC')
    def MC(premises, **kwargs):
        a = verify_arity(premises, 1)
        if not a.is_line():
            raise JustificationError('Invalid application of "MC".')

        match a.formula:
            case Not(Box(b)):
                return [Dia(Not(b))]
            case Dia(Not(b)):
                return [Not(Box(b))]
            case Not(Dia(b)):
                return [Box(Not(b))]
            case Box(Not(b)):
                return [Not(Dia(b))]
        
        raise JustificationError('Invalid application of "MC".')


class MLT(MLK):

    @Rules.add('RT')
    def RT(premises, scope, **kwargs):
        a = verify_arity(premises, 1)
        if not (a.is_line() and isinstance(a := a.formula, Box)):
            raise JustificationError('Invalid application of "RT".')
        
        lines = [obj.formula for obj in scope[1] if obj.is_line()]
        if lines.count(BoxMarker()) != 0:
            raise JustificationError('Invalid application of "RT".')
        return [a.inner]


class MLS4(MLT):

    @Rules.add('R4', strict=True)
    def R4(premises, scope, **kwargs):
        a = verify_arity(premises, 1)
        if not (a.is_line() and isinstance(a := a.formula, Box)):
            raise JustificationError('Invalid application of "R4".')
        
        lines = [obj.formula for obj in scope[1] if obj.is_line()]
        if lines.count(BoxMarker()) != 1:
            raise JustificationError('Invalid application of "R4".')
        return [a]


class MLS5(MLS4):

    @Rules.add('R5', strict=True)
    def R5(premises, scope, **kwargs):
        a = verify_arity(premises, 1)
        if not (a.is_line() and isinstance(a := a.formula, Not) 
                and isinstance(a.inner, Box)):
            raise JustificationError('Invalid application of "R5".')
        
        lines = [obj.formula for obj in scope[1] if obj.is_line()]
        if lines.count(BoxMarker()) != 1:
            raise JustificationError('Invalid application of "R5".')
        return [a]


def is_tfl_sentence(formula):
    match formula:
        case Falsum() | PropVar():
            return True
        case Not(a):
            return is_tfl_sentence(a)
        case And(a, b) | Or(a, b) | Imp(a, b) | Iff(a, b):
            return is_tfl_sentence(a) and is_tfl_sentence(b)
        case _:
            return False


def is_fol_formula(formula):
    # For now, not including prop vars
    match formula:
        case Falsum() | Pred() | Eq():
            return True
        case Not(a) | Forall(_, a) | Exists(_, a):
            return is_fol_formula(a)
        case And(a, b) | Or(a, b) | Imp(a, b) | Iff(a, b):
            return is_fol_formula(a) and is_fol_formula(b)
        case _:
            return False


def is_fol_sentence(formula):
    return is_fol_formula(formula) and not free_vars(formula)


def is_ml_sentence(formula):
    match formula:
        case Falsum() | PropVar():
            return True
        case Not(a) | Box(a) | Dia(a):
            return is_ml_sentence(a)
        case And(a, b) | Or(a, b) | Imp(a, b) | Iff(a, b):
            return is_ml_sentence(a) and is_ml_sentence(b)
        case _:
            return False


def terms(formula, free):
    match formula:
        case Pred(_, args):
            return set(args)
        case Eq(a, b):
            return {a, b}
        case Not(a) | Box(a) | Dia(a):
            return terms(a, free)
        case And(a, b) | Or(a, b) | Imp(a, b) | Iff(a, b):
            return terms(a, free) | terms(b, free)
        case Forall(v, a) | Exists(v, a):
            return terms(a, free) - {v} if free else terms(a, free)
        case _:
            return set()


def constants(formula):
    all_terms = terms(formula, free=False)
    return {t for t in all_terms if t.name in Const.names}


def free_vars(formula):
    free_terms = terms(formula, free=True)
    return {t for t in free_terms if t.name in Var.names}


def sub_terms(formula, terms, gen, ignore=lambda v: False):
    match formula:
        case Falsum():
            return Falsum()
        case Not(a):
            return Not(sub_terms(a, terms, gen, ignore))
        case And(a, b) | Or(a, b) | Imp(a, b) | Iff(a, b):
            a = sub_terms(a, terms, gen, ignore)
            b = sub_terms(b, terms, gen, ignore)
            return type(formula)(a, b)
        case Forall(v, a) | Exists(v, a):
            a = a if ignore(v) else sub_terms(a, terms - {v}, gen, ignore)
            return type(formula)(v, a)
        case Pred(s, args):
            args = tuple(gen() if arg in terms else arg for arg in args)
            return Pred(s, args)
        case Eq(a, b):
            a = gen() if a in terms else a
            b = gen() if b in terms else b
            return Eq(a, b)


class ProofObject:
    def is_line(self):
        return isinstance(self, Line)
    
    def is_subproof(self):
        return isinstance(self, Subproof)
    
    def is_strict_subproof(self):
        return self.is_subproof() and isinstance(self.assumption, BoxMarker)


@dataclass(frozen=True)
class Line(ProofObject):
    idx: int
    formula: Formula
    justification: Justification


class Subproof(ProofObject):
    def __init__(self, start_idx=None, assumption=None, context=None):
        if context is None:
            context = []

        seq = []
        if assumption:
            j = Justification(Rules.AS, ())
            line = Line(start_idx, assumption, j)
            seq.append(line)

        self.assumption = assumption
        self.context = context
        self.seq = seq

    @property
    def idx(self):
        seq = self.seq
        if not self.assumption:
            seq = self.context + seq
        if not seq:
            return (0, 0)
        start, end = seq[0], seq[-1]
        start_idx = start.idx if start.is_line() else start.idx[0]
        end_idx = end.idx if end.is_line() else end.idx[1]
        return (start_idx, end_idx)
    
    @property
    def conclusion(self):
        seq = self.seq
        if not seq:
            return None
        if self.assumption and len(seq) == 1:
            return None
        end = seq[-1]
        return end.formula if end.is_line() else None
    
    def add_line(self, formula, justification):
        seq = self.seq
        if seq and (end := seq[-1]).is_subproof():
            return end.add_line(formula, justification)
        return self._add_line_current(formula, justification)
    
    def begin_subproof(self, assumption):
        seq = self.seq
        if seq and (end := seq[-1]).is_subproof():
            return end.begin_subproof(assumption)
        return self._begin_subproof_current(assumption)

    def end_subproof(self, formula, justification):
        seq = self.seq
        if not (seq and (end := seq[-1]).is_subproof()):
            raise ProofActionError('No active subproof to close.')
        if end.seq[-1].is_subproof():
            return end.end_subproof(formula, justification)
        return self._add_line_current(formula, justification)

    def end_and_begin_subproof(self, assumption):
        seq = self.seq
        if not (seq and (end := seq[-1]).is_subproof()):
            raise ProofActionError('No active subproof to close.')
        if end.seq[-1].is_subproof():
            return end.end_and_begin_subproof(assumption)
        return self._begin_subproof_current(assumption)
    
    def delete_line(self):
        seq = self.seq
        if not seq:
            raise ProofActionError('No lines to delete.')
        if (end := seq[-1]).is_subproof() and len(end.seq) != 1:
            return end.delete_line()
        seq.pop()

    def retrieve_citations(self, citations, strict=False):
        scope = self.seq if strict else self.context + self.seq
        idx_map = {obj.idx: obj for obj in scope}
        premises = []
        for idx in citations:
            obj = idx_map.get(idx)
            if obj is None:
                raise JustificationError(f'Citation {idx} not in scope.')
            premises.append(obj)
        return premises
    
    def partition_scope(self, citations):
        citations = set(citations)
        scope = self.context + self.seq
        partitions, current = [], []

        for obj in scope:
            current.append(obj)
            if obj.idx in citations:
                partitions.append(current)
                current = []
        partitions.append(current)
        return partitions

    def match_schemes(self, formula, schemes):
        # print(f'Schemes: {', '.join(str(s) for s in schemes)}')
        return any(formula == s for s in schemes)
    
    def _add_line_current(self, formula, justification):
        rule, citations = justification.rule, justification.citations
        strict = self.is_strict_subproof() and rule not in Rules.strict
        premises = self.retrieve_citations(citations, strict)
        scope = self.partition_scope(citations)
        schemes = rule(premises, conclusion=formula, scope=scope)

        if not self.match_schemes(formula, schemes):
            raise InferenceError('Line not justified.')
        idx = self.idx[1] + 1
        line = Line(idx, formula, justification)
        self.seq.append(line)
    
    def _begin_subproof_current(self, assumption):
        idx = self.idx[1] + 1
        context = self.context + self.seq
        subproof = Subproof(idx, assumption, context)
        self.seq.append(subproof)

    def _collect_lines(self, depth=0):
        indent = '│ ' * depth
        seq = self.seq if self.assumption else self.context + self.seq
        bar_idx = 0 if self.assumption else len(self.context) - 1

        lines = []
        for idx, obj in enumerate(seq):
            if obj.is_line():
                formula = str(obj.formula)
                j = obj.justification
                lines.append((obj.idx, f'{indent}│ {formula}', j))
            else:
                lines.extend(obj._collect_lines(depth + 1))

            if idx == bar_idx:
                bar = f"{indent}├{'─' * (len(formula) + 2)}"
                lines.append(('', bar, ''))
            elif idx != len(seq) - 1:
                lines.append(('', f'{indent}│', ''))
        return lines


class Proof:
    def __init__(self, logic, premises, conclusion):
        self.logic = logic
        self.verify_formula(conclusion)

        context, idx = [], 1
        for p in premises:
            self.verify_formula(p)
            j = Justification(Rules.PR, ())
            context.append(Line(idx, p, j))
            idx += 1
        
        self.premises = premises
        self.conclusion = conclusion
        self.proof = Subproof(context=context)

    def __str__(self):
        lines = self.proof._collect_lines()
        if not lines:
            return ''
        width = max(len(l[1]) for l in lines)

        str_lines = []
        for idx, text, j in lines:
            str_line = f'{idx:>2} {text:<{width + 5}} {j}'
            str_lines.append(str_line)
        return '\n'.join(str_lines)

    def add_line(self, formula, justification):
        self.verify_formula(formula)
        self.verify_rule(justification.rule)
        self.proof.add_line(formula, justification)

    def begin_subproof(self, assumption):
        self.verify_assumption(assumption)
        self.proof.begin_subproof(assumption)

    def end_subproof(self, formula, justification):
        self.verify_formula(formula)
        self.verify_rule(justification.rule)
        self.proof.end_subproof(formula, justification)

    def end_and_begin_subproof(self, assumption):
        self.verify_assumption(assumption)
        self.proof.end_and_begin_subproof(assumption)

    def delete_line(self):
        self.proof.delete_line()

    def verify_formula(self, formula):
        if self.logic is TFL and is_tfl_sentence(formula):
            return
        if self.logic is FOL and is_fol_sentence(formula):
            return
        if issubclass(self.logic, MLK) and is_ml_sentence(formula):
            return
        raise Exception(
            f'"{formula}" is not a valid {self.logic.__name__} sentence.'
        )

    def verify_rule(self, rule):
        if not hasattr(self.logic, rule.func.__name__):
            raise Exception(
                f'"{rule}" is not a valid {self.logic.__name__} rule.'
            )

    def verify_assumption(self, assumption):
        if issubclass(self.logic, MLK) and isinstance(assumption, BoxMarker):
            return
        self.verify_formula(assumption)

    def is_complete(self):
        return self.proof.conclusion == self.conclusion
