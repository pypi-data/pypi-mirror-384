from .._generators import (  # noqa: TID252
    EqualityGenerator,
    EqualityKeyMappingGenerator,
    IsTypeGenerator,
    MappingGenerator,
    MappingSubsetGenerator,
    ObjectAttributesGenerator,
    OfTypeGenerator,
    OrderedGenerator,
    StringifiedGenerator,
    UniformMappingGenerator,
    UniformMappingSubsetGenerator,
    UniformOrderedGenerator,
    UnionGenerator,
    UnorderedGenerator,
    WithTypeGenerator,
)
from .generator_factory import GeneratorFactory


class BuiltInGeneratorFactory(GeneratorFactory):
    """
    Factory that has all built-in generators registered.
    """


BuiltInGeneratorFactory.register_generator(EqualityGenerator)
BuiltInGeneratorFactory.register_generator(EqualityKeyMappingGenerator)
BuiltInGeneratorFactory.register_generator(IsTypeGenerator)
BuiltInGeneratorFactory.register_generator(MappingGenerator)
BuiltInGeneratorFactory.register_generator(MappingSubsetGenerator)
BuiltInGeneratorFactory.register_generator(ObjectAttributesGenerator)
BuiltInGeneratorFactory.register_generator(OfTypeGenerator)
BuiltInGeneratorFactory.register_generator(OrderedGenerator)
BuiltInGeneratorFactory.register_generator(StringifiedGenerator)
BuiltInGeneratorFactory.register_generator(UniformOrderedGenerator)
BuiltInGeneratorFactory.register_generator(UniformMappingGenerator)
BuiltInGeneratorFactory.register_generator(UniformMappingSubsetGenerator)
BuiltInGeneratorFactory.register_generator(UnionGenerator)
BuiltInGeneratorFactory.register_generator(UnorderedGenerator)
BuiltInGeneratorFactory.register_generator(WithTypeGenerator)
