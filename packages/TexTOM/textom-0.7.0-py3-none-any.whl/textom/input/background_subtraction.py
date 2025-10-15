# choose a mode among the following
mode = 'linear' # options: 'linear' # 'chebyshev' # 'chebyshev_auto' # 'none'
# not used parameters will be ignored
order_chebyshev = 10 
# auto masking parameters ('chebyshev_auto')
pre_order=6 # chebyshev order for auto-masking (to smooth the curve)
k_sigma=2.0 # this measures how much the peak stands out from the data
peak_expand=2 # this should be about the width of the peaks
# choose q-range where the baseline should be drawn (can be important for 'chebyshev_auto' & 'chebyshev')
q_min=0 
q_max=100