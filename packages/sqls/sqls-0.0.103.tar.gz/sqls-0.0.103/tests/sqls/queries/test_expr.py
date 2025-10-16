# Copyright 2020 - 2025 Marko Durkovic
# SPDX-License-Identifier: Apache-2.0
"""Expression tests."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from sqls.queries import ExprFunction, ExprLiteral, Query
from sqls.queries.expr import Expr, ExprColumn, ExprTyped

if TYPE_CHECKING:
    from typing import TypeVar

    from sqls.interfaces import Transaction

    T = TypeVar('T')


async def evl(txn: Transaction, expr: ExprTyped[T]) -> T:
    """Evaluate expression."""
    query = Query().select(expr)
    res = await txn.exq(query)
    return res[0][0]


async def test_simple(txn: Transaction) -> None:
    """Test expressions."""
    with pytest.raises(NotImplementedError):
        Expr().__getsql__()

    nonbind = ExprLiteral("fo'o", bind=False)
    assert nonbind.__getsql__() == ("'fo''o'", ())
    assert await evl(txn, nonbind.typed(str)) == "fo'o"

    nonbind = ExprLiteral((1, 'x'), bind=False)
    assert nonbind.__getsql__() == ("(1, 'x')", ())

    assert str(ExprLiteral(1.0)) == 'Literal: 1.0'


@pytest.mark.skip
def test_unsupported() -> None:
    """Test expressions."""
    nonbind = ExprLiteral(((1, 2, 3), ExprLiteral((4, 5, 6))))  # type: ignore[arg-type]
    assert nonbind.__getsql__() == ('(?, (?, ?, ?))', ((1, 2, 3), 4, 5, 6))


def test_column() -> None:
    """Test expressions."""

    def format_col(scheme: str, table: str, col: str) -> str:
        return ExprColumn(scheme, table, col).__getsql__()[0]

    assert format_col('', '', '*') == '*'
    assert format_col('', 'tbl', 'col') == '"tbl"."col"'
    assert format_col('scheme', 'tbl', 'col') == '"scheme"."tbl"."col"'
    assert format_col('', 'tbl', 'co"l') == '"tbl"."co""l"'

    assert isinstance(ExprColumn('', 'tbl', 'col').typed(int), ExprTyped)


async def test_positive_negative(txn: Transaction) -> None:
    """Test expressions."""
    one = ExprLiteral(1)
    oneplusone = one + 1

    assert await evl(txn, one.positive().typed(int)) == 1
    assert await evl(txn, one.negative().typed(int)) == -1
    assert await evl(txn, oneplusone.negative().typed(int)) == -2


async def test_negate(txn: Transaction) -> None:
    """Test expressions."""
    one = ExprLiteral(1)
    true = ExprLiteral(True)

    assert await evl(txn, one.bitwise_negate().typed(int)) in [-2, 18446744073709551614]

    assert await evl(txn, true.negate().typed(int)) in [False, 0]


async def test_strconcat(txn: Transaction) -> None:
    """Test expressions."""
    strone = ExprLiteral('1.0')
    foobar = ExprLiteral('foo_bar')

    assert await evl(txn, strone.strconcat('foo').typed(str)) == '1.0foo'
    assert await evl(txn, strone.strconcat(foobar).typed(str)) == '1.0foo_bar'


async def test_arithmetic(txn: Transaction) -> None:
    """Test expressions."""
    one = ExprLiteral(1.0)
    oneint = ExprLiteral(1)
    oneplusone = oneint + 1

    assert await evl(txn, (one * 2).typed(int)) == 2
    assert await evl(txn, (one * oneplusone).typed(int)) == 2
    assert await evl(txn, (one / 2).typed(float)) == 0.5
    assert await evl(txn, (one / oneplusone).typed(float)) == 0.5
    assert await evl(txn, (one + 2).typed(int)) == 3
    assert await evl(txn, (one + oneplusone).typed(int)) == 3
    assert await evl(txn, (one - 2).typed(int)) == -1
    assert await evl(txn, (one - oneplusone).typed(int)) == -1
    assert await evl(txn, (oneint << 2).typed(int)) == 4
    assert await evl(txn, (oneint << oneplusone).typed(int)) == 4
    assert await evl(txn, (oneint * 15 >> 2).typed(int)) == 3
    assert await evl(txn, (oneint * 15 >> oneplusone).typed(int)) == 3
    assert await evl(txn, (oneint * 15 & 2).typed(int)) == 2
    assert await evl(txn, (oneint * 15 & oneplusone).typed(int)) == 2
    assert await evl(txn, (oneint * 16 | 2).typed(int)) == 18
    assert await evl(txn, (oneint * 16 | oneplusone).typed(int)) == 18

    assert await evl(txn, (one < 2).typed(bool)) == 1
    assert await evl(txn, (one < oneplusone).typed(bool)) == 1
    assert await evl(txn, (one <= 2).typed(bool)) == 1
    assert await evl(txn, (one <= oneplusone).typed(bool)) == 1
    assert await evl(txn, (one > 2).typed(bool)) == 0
    assert await evl(txn, (one > oneplusone).typed(bool)) == 0
    assert await evl(txn, (one >= 2).typed(bool)) == 0
    assert await evl(txn, (one >= oneplusone).typed(bool)) == 0
    assert await evl(txn, (one == 2).typed(bool)) == 0
    assert await evl(txn, (one == oneplusone).typed(bool)) == 0
    assert await evl(txn, (one != 2).typed(bool)) == 1
    assert await evl(txn, (one != oneplusone).typed(bool)) == 1


async def test_modulo(txn: Transaction) -> None:
    """Test expressions."""
    oneint = ExprLiteral(1)
    oneplusone = oneint + 1

    assert await evl(txn, (oneint * 5 % 2).typed(bool)) == 1
    assert await evl(txn, (oneint * 5 % oneplusone).typed(bool)) == 1


async def test_boolean_algebra(txn: Transaction) -> None:
    """Test expressions."""
    one = ExprLiteral(1.0)

    assert await evl(txn, (one != 2).and_(True).typed(bool)) == 1
    assert await evl(txn, (one != 2).and_(False).typed(bool)) == 0
    assert await evl(txn, (one != 2).and_(one == 2).typed(bool)) == 0
    assert await evl(txn, (one == 2).or_(True).typed(bool)) == 1
    assert await evl(txn, (one == 2).or_(False).typed(bool)) == 0
    assert await evl(txn, (one == 2).or_(one != 2).typed(bool)) == 1


async def test_cast(txn: Transaction) -> None:
    """Test expressions."""
    one = ExprLiteral(1.0)

    assert await evl(txn, (one == 2).cast('TEXT').typed(str)) in ['false', '0']


async def test_like(txn: Transaction) -> None:
    """Test expressions."""
    foobar = ExprLiteral('foo_bar')

    assert await evl(txn, foobar.like(foobar).typed(bool)) == 1
    assert await evl(txn, foobar.like('foo%').typed(bool)) == 1
    assert await evl(txn, foobar.not_like('foo').typed(bool)) == 1

    assert await evl(txn, foobar.like('fo___ar').typed(bool)) == 1
    assert await evl(txn, foobar.like('foo_bar').typed(bool)) == 1
    assert await evl(txn, foobar.like('_oo!_ba_', escape='!').typed(bool)) == 1


@pytest.mark.parametrize(
    'txn',
    [
        'sqlite',
        pytest.param('postgres', marks=pytest.mark.skip(reason='unsupported')),
        pytest.param('mysql', marks=pytest.mark.skip(reason='unsupported')),
    ],
    indirect=True,
)
async def test_glob(txn: Transaction) -> None:
    """Test expressions."""
    foobar = ExprLiteral('foo_bar')

    assert await evl(txn, foobar.glob('foo*').typed(bool)) == 1
    assert await evl(txn, foobar.not_glob('*foo').typed(bool)) == 1


@pytest.mark.parametrize(
    'txn',
    [
        pytest.param('sqlite', marks=pytest.mark.skip(reason='needs c-extension')),
        'postgres',
        'mysql',
    ],
    indirect=True,
)
async def test_regex(txn: Transaction) -> None:
    """Test expressions."""
    foobar = ExprLiteral('foo_bar')

    assert await evl(txn, foobar.regexp('^foo.*$').typed(bool)) == 1
    assert await evl(txn, foobar.not_regexp('^foo$').typed(bool)) == 1


@pytest.mark.parametrize(
    'txn',
    [
        pytest.param('sqlite', marks=pytest.mark.skip(reason='raises by default')),
        pytest.param('postgres', marks=pytest.mark.skip(reason='unsupported')),
        pytest.param('mysql', marks=pytest.mark.skip(reason='unsupported')),
    ],
    indirect=True,
)
async def test_match(txn: Transaction) -> None:
    """Test expressions."""
    foobar = ExprLiteral('foo_bar')

    assert await evl(txn, foobar.match('foo*').typed(bool)) == 1
    assert await evl(txn, foobar.not_match('*foo').typed(bool)) == 1


async def test_null(txn: Transaction) -> None:
    """Test expressions."""
    one = ExprLiteral(1.0)
    null = ExprLiteral(None)

    assert await evl(txn, one.is_null().typed(bool)) == 0
    assert await evl(txn, one.not_null().typed(bool)) == 1

    assert await evl(txn, null.is_null().typed(bool)) == 1
    assert await evl(txn, null.not_null().typed(bool)) == 0

    assert await evl(txn, null.is_(null).typed(bool)) == 1
    assert await evl(txn, null.is_not(null).typed(bool)) == 0


@pytest.mark.parametrize(
    'txn',
    [
        'sqlite',
        pytest.param('postgres', marks=pytest.mark.skip(reason='unsupported')),
        pytest.param('mysql', marks=pytest.mark.skip(reason='unsupported')),
    ],
    indirect=True,
)
async def test_null_is(txn: Transaction) -> None:
    """Test expressions."""
    null = ExprLiteral(None)

    assert await evl(txn, null.is_(0).typed(bool)) == 0
    assert await evl(txn, null.is_not(0).typed(bool)) == 1


async def test_between(txn: Transaction) -> None:
    """Test expressions."""
    one = ExprLiteral(1.0)

    assert await evl(txn, (one + 7).between(4, 12).typed(bool)) == 1
    assert await evl(txn, (one + 7).between(one + 3, one + 11).typed(bool)) == 1
    assert await evl(txn, one.not_between(2, 3).typed(bool)) == 1
    assert await evl(txn, one.not_between(one + 1, one + 2).typed(bool)) == 1


async def test_in(txn: Transaction) -> None:
    """Test expressions."""
    one = ExprLiteral(1.0)

    assert await evl(txn, one.in_((1, 3, 5)).typed(bool)) == 1
    assert await evl(txn, one.in_(ExprLiteral((1, 3, 5))).typed(bool)) == 1
    assert await evl(txn, one.not_in((2, 4, 6)).typed(bool)) == 1
    assert await evl(txn, one.not_in(ExprLiteral((2, 4, 6))).typed(bool)) == 1


@pytest.mark.parametrize(
    'txn',
    [
        'sqlite',
        pytest.param('postgres', marks=pytest.mark.skip(reason='unsupported')),
        pytest.param('mysql', marks=pytest.mark.skip(reason='unsupported')),
    ],
    indirect=True,
)
async def test_json_get(txn: Transaction) -> None:
    """Test expressions."""
    json = ExprLiteral('{"a":42, "b":"foo", "c":[1,2]}')

    assert await evl(txn, json.json_get('$').typed(str)) == '{"a":42,"b":"foo","c":[1,2]}'
    assert await evl(txn, json.json_get('a').typed(str)) == '42'
    assert await evl(txn, json.json_get(ExprLiteral('a')).typed(str)) == '42'
    assert await evl(txn, json.json_get('b').typed(str)) == '"foo"'
    assert await evl(txn, json.json_get('c').typed(str)) == '[1,2]'
    assert await evl(txn, json.json_get('$.c[1]').typed(str)) == '2'
    assert await evl(txn, json.json_get('$.c').json_get('[1]').typed(str)) == '2'
    assert await evl(txn, json.json_get('$.c').json_get('[#-1]').typed(str)) == '2'


@pytest.mark.parametrize(
    'txn',
    [
        'sqlite',
        pytest.param('postgres', marks=pytest.mark.skip(reason='unsupported')),
        pytest.param('mysql', marks=pytest.mark.skip(reason='unsupported')),
    ],
    indirect=True,
)
async def test_json_get_value(txn: Transaction) -> None:
    """Test expressions."""
    json = ExprLiteral('{"a":42, "b":"foo", "c":[1,2]}')

    assert await evl(txn, json.json_get_value('$').typed(str)) == '{"a":42,"b":"foo","c":[1,2]}'
    assert await evl(txn, json.json_get_value('a').typed(int)) == 42
    assert await evl(txn, json.json_get_value(ExprLiteral('a')).typed(int)) == 42
    assert await evl(txn, json.json_get_value('b').typed(str)) == 'foo'
    assert await evl(txn, json.json_get_value('c').typed(str)) == '[1,2]'
    assert await evl(txn, json.json_get_value('$.c[1]').typed(int)) == 2
    assert await evl(txn, json.json_get('$.c').json_get_value('[1]').typed(int)) == 2
    assert await evl(txn, json.json_get('$.c').json_get_value('[#-1]').typed(int)) == 2


async def test_subq_exists(txn: Transaction) -> None:
    """Test expressions."""
    assert await evl(txn, Query().values((1,)).subq().exists().typed(int)) == 1
    assert await evl(txn, Query().values((1,)).subq().not_exists().typed(int)) == 0


async def test_alias(txn: Transaction) -> None:
    """Test expressions."""
    one = ExprLiteral(1.0)

    assert await evl(txn, (one + 10).as_('foo').typed(int)) == 11


async def test_function(txn: Transaction) -> None:
    """Test expressions."""
    one = ExprLiteral(1.0)

    assert await evl(txn, ExprFunction('SUM', one).typed(int)) == 1
