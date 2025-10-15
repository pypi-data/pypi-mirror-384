# -*- coding: utf-8 -*-
"""
---------------------------------------------
Created on 2025/6/10 17:43
@author: ZhangYundi
@email: yundi.xxii@outlook.com
@description: 
---------------------------------------------
"""
import lidb

from quda.qdf.expr import Expr
from quda.qdf import to_lazy, from_polars

def test_qdf():
    quote_tb = "mc/stock_tick_cleaned"
    quote = lidb.scan(quote_tb).filter(freq="3s", date="2025-05-06", asset="688111")
    expr = "itd_mean(greater(0, -itd_diff(ask_v1, 1)), 5)"
    res = to_lazy(quote).sql(expr).collect()
    print(res)


if __name__ == '__main__':
    # expr = "a>0?b:Null as d"
    # res = Expr(expr)
    # print(res)
    test_qdf()