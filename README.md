# TokimekiMemorialTranslated


### Setup
```
git submodule sync
git submodule update --init --recursive --jobs 0
```

add this to line 7881 in ~/Code/Avocado/externals/catch/single_include/catch2/catch.hpp
```
#if defined(__i386__) || defined(__x86_64__)
    #define CATCH_TRAP() __asm__("int $3\n" : : ) [> NOLINT <]
#elif defined(__aarch64__)
    #define CATCH_TRAP()  __asm__(".inst 0xd4200000")
#endif
```
