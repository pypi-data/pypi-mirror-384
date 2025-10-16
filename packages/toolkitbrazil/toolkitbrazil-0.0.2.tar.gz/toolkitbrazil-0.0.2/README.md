![PyPI - License](https://img.shields.io/pypi/l/toolkitbrazil)
![PyPI - Version](https://img.shields.io/pypi/v/toolkitbrazil)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/toolkitbrazil)
![](https://img.shields.io/badge/Latest%20Release-Oct%2015,%202025-blue)
[![Github](https://img.shields.io/badge/github-toolkitbrazil-blue)](https://github.com/coloric/toolkitbrazil)
<br>
![Pepy Total Downloads](https://img.shields.io/pepy/dt/toolkitbrazil)
![PyPI - Downloads](https://img.shields.io/pypi/dd/toolkitbrazil)
![PyPI - Downloads](https://img.shields.io/pypi/dw/toolkitbrazil)
![PyPI - Downloads](https://img.shields.io/pypi/dm/toolkitbrazil)


# Introduction

A Python module with a collection of useful tools for Brazilians (and anyone else who wants to use it).
Take a look at [CHANGELOG.md](https://github.com/coloric/toolkitbrazil/blob/main/CHANGELOG.md) for the changes.


# Brief History
I started studying Python recently and wanted to do something that would be useful. Enjoy `toolkitbrazil`.


# Overview

Here's a quick overview of what the library has at the moment:

- Random generation of CPF and CNPJ numbers
- CPF and CNPJ validation
- Checks which state a DDD belongs to
- Checks if a year is a leap year
- Calculates the date of Easter Sunday or Carnival Tuesday for a given year
- Check if a specific date is Easter Sunday or Carnival Tuesday
- Returns the capital of a state
- Returns city and state os a zip code
- String cleaner


## How to install

pip install toolkitbrazil


## Usage

```python
import toolkitbrazil as tkb

# Remove diacritics, non alpha chars, multiple spaces and convert string to upper case
print(tkb.strClean('A héalt#hy  dìet is    esse&ntiãl  for    go(od heàlth and    nutrition  '))
# Return: 'A HEALTHY DIET IS ESSENTIAL FOR GOOD HEALTH AND NUTRITION'

# Generate a random CPF
print(tkb.rngCPF())
# Sample return: 75269169703

# Generate a random CPF of specific UF
print(tkb.rngCPF('SP'))
# Sample return: 27039729890

# Validate a CPF
print(tkb.valCPF(75269169703))
# Return: True

# Generate a random CNPJ of the headquarters (branch 0001)
print(tkb.rngCNPJ())
# Sample return: 86978319000101

# Generate a random CNPJ of a branch (any branch)
print(tkb.rngCNPJfiliais())
# Sample return: 94318840326682

# Generate a random CNPJ of a desired branch (1 to 9999)
print(tkb.rngCNPJfiliais(187))
# Sample return: 50138939018728

# Validate a CNPJ
print(tkb.valCNPJ(86978319000101))
# Return: True

# Check the UF of the CPF
print(tkb.ufCPF(75269169703))
# Return: ['ES', 'RJ']

# Check the UF of the DDD or phone number (using first two digits of any number)
print(tkb.ufDDD(61))
# Return: ['DF', 'GO']
print(tkb.ufDDD(11987654321))
# Return: ['SP']

# Check the capital of a UF
print(tkb.ufCapital('SP'))
# Return ['SAO PAULO', 'SP']

# Validate a CPF and check its UF
print(tkb.valCPFuf(75269169703, 'SP'))
# Return False (it's a valid CPF but from another UF)

# Check if it is a leap year
print(tkb.valBissexto(2024))
# Return: True

# Calculates the date of Easter Sunday for a given year
print(tkb.dtPascoa(2025))
# Return 2025-04-20

# Check if a specific date is Easter Sunday
print(tkb.valPascoa(date(2025, 4, 20)))
# Return: True

# Calculates the date of Carnival Tuesday for a given year
print(tkb.dtCarnaval(2025))
# Return 2025-03-04

# Check if a specific date is Carnival Tuesday
print(tkb.valCarnaval(date(2025, 3, 4)))
# Return: True

# Check a zip code and return a list containing city and state [cidade, uf]
print(tkb.ufCep('01001-000'))
# Return ['SAO PAULO', 'SP']
print(tkb.ufCep(80020000))
# Return ['CURITIBA', 'PR']
```

## Authors

Ricardo Colombani - [@coloric](https://www.github.com/coloric)


## License

[MIT](https://choosealicense.com/licenses/mit/)