from .core_grammar import CoreGrammar
from .dependency_grammar import DependencyGrammar
from .extended_grammar import ExtendedGrammar

GRAMMARS = {
    "Core Grammar": CoreGrammar,
    "Extended Grammar": ExtendedGrammar,
    "Dependency Grammar": DependencyGrammar,
}
