#!/bin/bash

# These are basic happy path tests that run pricehist from the command line and
# confirm that the results come out as expected. They help ensure that the main
# endpoints for each source are still working.

# Run this from the project root.

export ALPHAVANTAGE_API_KEY="TEST_KEY_$RANDOM"
cmd_prefix="poetry run"

passed=0
failed=0
skipped=0

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

skip_test(){
  name=$1
  cmd=$2
  echo "TEST: $name"
  echo "  Action: $cmd"
  echo "  Result: SKIPPED!"
  skipped=$((skipped+1))
  echo
}

report(){
  total=$((passed+failed))
  if [[ "$skipped" -eq "0" ]]; then
    skipped_str="none"
  else
    skipped_str="$skipped"
  fi
  if [[ "$failed" -eq "0" ]]; then
    echo "SUMMARY: $passed tests passed, none failed, $skipped_str skipped"
  else
    echo "SUMMARY: $failed/$total tests failed, $skipped_str skipped"
    exit 1
  fi
}

name="Alpha Vantage stocks"
cmd="pricehist fetch alphavantage TSLA -s 2021-01-04 -e 2021-01-08"
read -r -d '' expected <<END
date,base,quote,amount,source,type
2021-01-04,TSLA,USD,729.7700,alphavantage,close
2021-01-05,TSLA,USD,735.1100,alphavantage,close
2021-01-06,TSLA,USD,755.9800,alphavantage,close
2021-01-07,TSLA,USD,816.0400,alphavantage,close
2021-01-08,TSLA,USD,880.0200,alphavantage,close
END
run_test "$name" "$cmd" "$expected"

name="Alpha Vantage physical currency"
cmd="pricehist fetch alphavantage AUD/EUR -s 2021-01-10 -e 2021-01-14"
read -r -d '' expected <<END
date,base,quote,amount,source,type
2021-01-10,AUD,EUR,0.63313,alphavantage,close
2021-01-11,AUD,EUR,0.63374,alphavantage,close
2021-01-12,AUD,EUR,0.63684,alphavantage,close
2021-01-13,AUD,EUR,0.63686,alphavantage,close
2021-01-14,AUD,EUR,0.63984,alphavantage,close
END
run_test "$name" "$cmd" "$expected"

name="Alpha Vantage digital currency"
cmd="pricehist fetch alphavantage BTC/USD -s 2024-07-01 -e 2024-07-05"
read -r -d '' expected <<END
date,base,quote,amount,source,type
2024-07-01,BTC,USD,62830.13000000,alphavantage,close
2024-07-02,BTC,USD,62040.22000000,alphavantage,close
2024-07-03,BTC,USD,60145.01000000,alphavantage,close
2024-07-04,BTC,USD,57042.14000000,alphavantage,close
2024-07-05,BTC,USD,56639.43000000,alphavantage,close
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
WARNING This source is deprecated. Data stops at 2022-07-10.
date,base,quote,amount,source,type
2021-01-04,BTC,EUR,26135.4901,coindesk,close
2021-01-05,BTC,EUR,27677.9141,coindesk,close
2021-01-06,BTC,EUR,29871.4301,coindesk,close
2021-01-07,BTC,EUR,32183.1594,coindesk,close
2021-01-08,BTC,EUR,33238.5724,coindesk,close
END
skip_test "$name" "$cmd" "$expected"

name="CoinMarketCap"
cmd="pricehist fetch coinmarketcap BTC/EUR -s 2021-01-04 -e 2021-01-08"
read -r -d '' expected <<END
date,base,quote,amount,source,type
2021-01-04,BTC,EUR,25330.6611989461305,coinmarketcap,mid
2021-01-05,BTC,EUR,26320.957584331295,coinmarketcap,mid
2021-01-06,BTC,EUR,28571.407214265565,coinmarketcap,mid
2021-01-07,BTC,EUR,31200.6391028267445,coinmarketcap,mid
2021-01-08,BTC,EUR,32154.244768031175,coinmarketcap,mid
END
skip_test "$name" "$cmd" "$expected"

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
2021-01-04,TSLA,USD,243.256668,yahoo,adjclose
2021-01-05,TSLA,USD,245.036667,yahoo,adjclose
2021-01-06,TSLA,USD,251.993332,yahoo,adjclose
2021-01-07,TSLA,USD,272.013336,yahoo,adjclose
2021-01-08,TSLA,USD,293.339996,yahoo,adjclose
END
run_test "$name" "$cmd" "$expected"

report
