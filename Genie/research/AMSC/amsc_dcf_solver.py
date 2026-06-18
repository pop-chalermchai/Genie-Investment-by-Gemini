# Extended Reverse DCF Solver for AMSC
# Christian, Forensic Auditor

def calculate_ev(fcf_0, growth, r, g):
    pv_fcf = 0.0
    for t in range(1, 11):
        fcf_t = fcf_0 * ((1.0 + growth) ** t)
        pv_fcf += fcf_t / ((1.0 + r) ** t)
    fcf_10 = fcf_0 * ((1.0 + growth) ** 10)
    tv = (fcf_10 * (1.0 + g)) / (r - g)
    pv_tv = tv / ((1.0 + r) ** 10)
    return pv_fcf + pv_tv

def solve_growth_rate(target_ev, fcf_0, r, g):
    low = -0.99
    high = 5.0
    tol = 1e-12
    max_iter = 100
    for _ in range(max_iter):
        mid = (low + high) / 2.0
        ev = calculate_ev(fcf_0, mid, r, g)
        if abs(ev - target_ev) < tol:
            return mid
        if ev < target_ev:
            low = mid
        else:
            high = mid
    return mid

def main():
    price = 40.46
    shares = 47.7 * 1e6
    equity_val = price * shares
    
    r = 0.218
    g = 0.03
    fcf_bases = [30.0, 50.0, 80.0]
    
    cases = [
        {"name": "Case 1: Core Net Debt (Net Cash = -$136.7M, Net Debt = +$136.7M)", "net_debt": 136.7 * 1e6},
        {"name": "Case 2: Debt-Free Baseline (Net Debt = $0)", "net_debt": 0.0},
        {"name": "Case 3: Positive Net Cash (Net Cash = +$136.7M, Net Debt = -$136.7M)", "net_debt": -136.7 * 1e6}
    ]
    
    for case in cases:
        target_ev = equity_val + case["net_debt"]
        print(f"\n{case['name']} (Target EV: ${target_ev/1e6:,.2f}M)")
        print("-" * 80)
        print(f"{'Starting FCF Base':<20} | {'Implied Growth Rate':<22} | {'Implied Year 10 FCF':<20}")
        print("-" * 80)
        for fcf in fcf_bases:
            fcf_0_val = fcf * 1e6
            growth = solve_growth_rate(target_ev, fcf_0_val, r, g)
            fcf_10 = fcf_0_val * ((1.0 + growth) ** 10)
            print(f"${fcf:<18.1f}M | {growth * 100:>20.4f}% | ${fcf_10 / 1e6:>18.2f}M")
        print("-" * 80)

if __name__ == "__main__":
    main()
