#!/bin/bash

# These are basic happy path tests that run pricehist from the command line and
# confirm that the results come out as expected. They help ensure that the main
# endpoints for each source are still working.

# Run this from the project root.

export ALPHAVANTAGE_API_KEY="TEST_KEY_$RANDOM"
cmd_prefix="poetry run"

passed=0
failed=0

run_test(){
  name=$1
  cmd=$2
  expected=$3
  echo    "TEST: $name"
  echo    "  Action: $cmd"
  echo -n "  Result: "
  full_cmd="$cmd_prefix $cmd"
  actual=$($full_cmd 2>&1)
  if [[ "$actual" == "$expected" ]]; then
    passed=$((passed+1))
    echo "passed, output as expected"
  else
    failed=$((failed+1))
    echo "failed, output differs as follows..."
    echo
    diff <(echo "$expected") <(echo "$actual")
  fi
  echo
}

report(){
  total=$((passed+failed))
  if [[ "$failed" -eq "0" ]]; then
    echo "SUMMARY: $passed tests passed, none failed"
  else
    echo "SUMMARY: $failed/$total tests failed"
    exit 1
  fi
}

name="Alpha Vantage stocks"
cmd="pricehist fetch alphavantage TSLA -s 2021-01-04 -e 2021-01-08"
read -r -d '' expected <<END
date,base,quote,amount,source,type
2021-01-04,TSLA,USD,729.77,alphavantage,close
2021-01-05,TSLA,USD,735.11,alphavantage,close
2021-01-06,TSLA,USD,755.98,alphavantage,close
2021-01-07,TSLA,USD,816.04,alphavantage,close
2021-01-08,TSLA,USD,880.02,alphavantage,close
END
run_test "$name" "$cmd" "$expected"


name="Alpha Vantage physical currency"
cmd="pricehist fetch alphavantage AUD/EUR -s 2021-01-04 -e 2021-01-08"
read -r -d '' expected <<END
date,base,quote,amount,source,type
2021-01-04,AUD,EUR,0.62558,alphavantage,close
2021-01-05,AUD,EUR,0.63086,alphavantage,close
2021-01-06,AUD,EUR,0.63306,alphavantage,close
2021-01-07,AUD,EUR,0.63284,alphavantage,close
2021-01-08,AUD,EUR,0.63360,alphavantage,close
END
run_test "$name" "$cmd" "$expected"

name="Alpha Vantage digital currency"
cmd="pricehist fetch alphavantage BTC/USD -s 2021-01-04 -e 2021-01-08"
read -r -d '' expected <<END
date,base,quote,amount,source,type
2021-01-04,BTC,USD,31988.71000000,alphavantage,close
2021-01-05,BTC,USD,33949.53000000,alphavantage,close
2021-01-06,BTC,USD,36769.36000000,alphavantage,close
2021-01-07,BTC,USD,39432.28000000,alphavantage,close
2021-01-08,BTC,USD,40582.81000000,alphavantage,close
END
run_test "$name" "$cmd" "$expected"

name="Bank of Canada"
cmd="pricehist fetch bankofcanada CAD/USD -s 2021-01-04 -e 2021-01-08"
read -r -d '' expected <<END
date,base,quote,amount,source,type
2021-01-04,CAD,USD,0.7843,bankofcanada,default
2021-01-05,CAD,USD,0.7870,bankofcanada,default
2021-01-06,CAD,USD,0.7883,bankofcanada,default
2021-01-07,CAD,USD,0.7870,bankofcanada,default
2021-01-08,CAD,USD,0.7871,bankofcanada,default
END
run_test "$name" "$cmd" "$expected"

name="Coinbase Pro"
cmd="pricehist fetch coinbasepro BTC/EUR -s 2021-01-04 -e 2021-01-08"
read -r -d '' expected <<END
date,base,quote,amount,source,type
2021-01-04,BTC,EUR,24127,coinbasepro,mid
2021-01-05,BTC,EUR,26201.31,coinbasepro,mid
2021-01-06,BTC,EUR,28527.005,coinbasepro,mid
2021-01-07,BTC,EUR,31208.49,coinbasepro,mid
2021-01-08,BTC,EUR,32019,coinbasepro,mid
END
run_test "$name" "$cmd" "$expected"

name="CoinDesk Bitcoin Price Index"
cmd="pricehist fetch coindesk BTC/EUR -s 2021-01-04 -e 2021-01-08"
read -r -d '' expected <<END
date,base,quote,amount,source,type
2021-01-04,BTC,EUR,26135.4901,coindesk,close
2021-01-05,BTC,EUR,27677.9141,coindesk,close
2021-01-06,BTC,EUR,29871.4301,coindesk,close
2021-01-07,BTC,EUR,32183.1594,coindesk,close
2021-01-08,BTC,EUR,33238.5724,coindesk,close
END
run_test "$name" "$cmd" "$expected"

name="CoinMarketCap"
cmd="pricehist fetch coinmarketcap BTC/EUR -s 2021-01-04 -e 2021-01-08"
read -r -d '' expected <<END
date,base,quote,amount,source,type
2021-01-04,BTC,EUR,25329.110170161484,coinmarketcap,mid
2021-01-05,BTC,EUR,26321.26752264663,coinmarketcap,mid
2021-01-06,BTC,EUR,28572.211551075297,coinmarketcap,mid
2021-01-07,BTC,EUR,31200.894541155460,coinmarketcap,mid
2021-01-08,BTC,EUR,32155.0183793871585,coinmarketcap,mid
END
run_test "$name" "$cmd" "$expected"

name="European Central Bank"
cmd="pricehist fetch ecb EUR/JPY -s 2021-01-04 -e 2021-01-08"
read -r -d '' expected <<END
date,base,quote,amount,source,type
2021-01-04,EUR,JPY,126.62,ecb,reference
2021-01-05,EUR,JPY,126.25,ecb,reference
2021-01-06,EUR,JPY,127.03,ecb,reference
2021-01-07,EUR,JPY,127.13,ecb,reference
2021-01-08,EUR,JPY,127.26,ecb,reference
END
run_test "$name" "$cmd" "$expected"

name="Yahoo! Finance"
cmd="pricehist fetch yahoo TSLA -s 2021-01-04 -e 2021-01-08"
read -r -d '' expected <<END
date,base,quote,amount,source,type
2021-01-04,TSLA,USD,729.770020,yahoo,adjclose
2021-01-05,TSLA,USD,735.109985,yahoo,adjclose
2021-01-06,TSLA,USD,755.979980,yahoo,adjclose
2021-01-07,TSLA,USD,816.039978,yahoo,adjclose
2021-01-08,TSLA,USD,880.020020,yahoo,adjclose
END
run_test "$name" "$cmd" "$expected"

report
