"""
Command-line interface for stockcharts screener.
"""
import argparse
import sys
from stockcharts.screener.screener import screen_nasdaq, ScreenResult
from stockcharts.screener.nasdaq import get_nasdaq_tickers
from stockcharts.data.fetch import fetch_ohlc
from stockcharts.charts.heiken_ashi import heiken_ashi
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle


def main_screen():
    """
    CLI entry point for NASDAQ screening.
    """
    parser = argparse.ArgumentParser(
        description='Screen NASDAQ stocks for Heiken Ashi color changes',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Screen for green reversals (red→green) on daily charts
  stockcharts-screen --color green --changed-only

  # Find red reversals with volume filter (swing trading)
  stockcharts-screen --color red --changed-only --min-volume 500000

  # Day trading setup: 1-hour charts with high volume
  stockcharts-screen --color green --period 1h --lookback 1mo --min-volume 2000000

  # Weekly analysis over 6 months
  stockcharts-screen --color green --period 1wk --lookback 6mo

  # Custom date range
  stockcharts-screen --color green --start 2024-01-01 --end 2024-12-31
        """
    )
    
    parser.add_argument(
        '--color', 
        choices=['red', 'green'], 
        default='green',
        help='Filter by current Heiken Ashi candle color (default: green)'
    )
    
    parser.add_argument(
        '--period', 
        default='1d',
        help='Data aggregation period: 1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo (default: 1d)'
    )
    
    parser.add_argument(
        '--lookback', 
        default='3mo',
        help='How far back to fetch data: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max (default: 3mo)'
    )
    
    parser.add_argument(
        '--start',
        help='Start date in YYYY-MM-DD format (overrides --lookback)'
    )
    
    parser.add_argument(
        '--end',
        help='End date in YYYY-MM-DD format (defaults to today)'
    )
    
    parser.add_argument(
        '--changed-only',
        action='store_true',
        help='Only show stocks where color changed in the most recent candle'
    )
    
    parser.add_argument(
        '--min-volume',
        type=int,
        default=0,
        help='Minimum average daily volume (e.g., 500000 for swing trading)'
    )
    
    parser.add_argument(
        '--min-price',
        type=float,
        default=None,
        help='Minimum stock price in dollars (e.g., 5.0 or 10.0 to filter out penny stocks)'
    )
    
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Maximum number of tickers to screen (default: all ~5,120 NASDAQ stocks)'
    )
    
    parser.add_argument(
        '--output',
        default='results/nasdaq_screen.csv',
        help='Output CSV file path (default: results/nasdaq_screen.csv)'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Show detailed error messages for each ticker'
    )
    
    args = parser.parse_args()
    
    print(f"Screening NASDAQ stocks for {args.color} Heiken Ashi candles...")
    print(f"Period: {args.period}, Lookback: {args.lookback}")
    if args.min_volume > 0:
        print(f"Minimum volume: {args.min_volume:,} shares/day")
    if args.min_price is not None:
        print(f"Minimum price: ${args.min_price:.2f}")
    if args.changed_only:
        print("Filtering for color changes only")
    if args.limit:
        print(f"Limiting to first {args.limit} tickers")
    print()
    
    results = screen_nasdaq(
        color_filter=args.color,
        period=args.period,
        lookback=args.lookback,
        start=args.start,
        end=args.end,
        changed_only=args.changed_only,
        min_volume=args.min_volume,
        min_price=args.min_price,
        limit=args.limit,
        debug=args.debug
    )
    
    # Save results to CSV
    if results:
        import os
        import pandas as pd
        
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        
        df = pd.DataFrame([{
            'ticker': r.ticker,
            'color': r.color,
            'ha_open': r.ha_open,
            'ha_close': r.ha_close,
            'last_date': r.last_date,
            'period': r.interval,
            'color_changed': r.color_changed,
            'avg_volume': r.avg_volume
        } for r in results])
        
        df.to_csv(args.output, index=False)
        print(f"\nFound {len(results)} stocks matching criteria")
        print(f"Results saved to: {args.output}")
    else:
        print(f"\nNo stocks found matching criteria")
    
    return 0


def main_plot():
    """
    CLI entry point for plotting Heiken Ashi charts from CSV results.
    """
    parser = argparse.ArgumentParser(
        description='Generate Heiken Ashi charts from screener results',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Plot all results from default location
  stockcharts-plot

  # Plot from specific CSV file
  stockcharts-plot --input results/green_reversals.csv

  # Save charts to specific directory
  stockcharts-plot --output-dir my_charts/
        """
    )
    
    parser.add_argument(
        '--input',
        default='results/nasdaq_screen.csv',
        help='Input CSV file from screener (default: results/nasdaq_screen.csv)'
    )
    
    parser.add_argument(
        '--output-dir',
        default='charts/',
        help='Output directory for chart images (default: charts/)'
    )
    
    parser.add_argument(
        '--period',
        default='1d',
        help='Data aggregation period (default: 1d)'
    )
    
    parser.add_argument(
        '--lookback',
        default='3mo',
        help='Historical data lookback (default: 3mo)'
    )
    
    args = parser.parse_args()
    
    import pandas as pd
    import os
    
    if not os.path.exists(args.input):
        print(f"Error: Input file not found: {args.input}")
        return 1
    
    os.makedirs(args.output_dir, exist_ok=True)
    
    df = pd.read_csv(args.input)
    tickers = df['ticker'].tolist()
    
    print(f"Generating Heiken Ashi charts for {len(tickers)} stocks...")
    print(f"Output directory: {args.output_dir}")
    print()
    
    for i, ticker in enumerate(tickers, 1):
        print(f"[{i}/{len(tickers)}] Plotting {ticker}...", end=' ')
        
        try:
            data = fetch_ohlc(ticker, period=args.period, lookback=args.lookback)
            if data is None or data.empty:
                print("❌ No data")
                continue
            
            ha_data = heiken_ashi(data)
            
            # Create chart
            fig, ax = plt.subplots(figsize=(14, 7))
            
            # Convert datetime index to matplotlib dates
            dates = mdates.date2num(ha_data.index.to_pydatetime())
            
            for idx in range(len(ha_data)):
                date = dates[idx]
                row = ha_data.iloc[idx]
                color = 'green' if row['HA_Close'] >= row['HA_Open'] else 'red'
                
                # Candle body
                body_height = abs(row['HA_Close'] - row['HA_Open'])
                body_bottom = min(row['HA_Open'], row['HA_Close'])
                rect = Rectangle((date - 0.4, body_bottom), 0.8, body_height,
                               facecolor=color, edgecolor='black', linewidth=0.5)
                ax.add_patch(rect)
                
                # Wicks
                ax.plot([date, date], 
                       [row['HA_Low'], body_bottom], 
                       color='black', linewidth=0.5)
                ax.plot([date, date], 
                       [body_bottom + body_height, row['HA_High']], 
                       color='black', linewidth=0.5)
            
            # Format x-axis with dates
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            ax.xaxis.set_major_locator(mdates.AutoDateLocator())
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
            
            ax.set_xlim(dates[0] - 1, dates[-1] + 1)
            ax.set_ylim(ha_data['HA_Low'].min() * 0.95, ha_data['HA_High'].max() * 1.05)
            ax.set_xlabel('Date')
            ax.set_ylabel('Price ($)')
            ax.set_title(f'{ticker} - Heiken Ashi ({args.period})')
            ax.grid(True, alpha=0.3)
            
            output_path = os.path.join(args.output_dir, f'{ticker}_{args.period}.png')
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            plt.close()
            
            print(f"✓ Saved to {output_path}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print(f"\nCompleted! Charts saved to {args.output_dir}")
    return 0


if __name__ == '__main__':
    sys.exit(main_screen())
