(defproject strategify "0.1.0"
  :description "Clojure Strategy Synthesizer for Strategify"
  :url "https://github.com/SpectreDeath/Strategify"
  :license {:name "MIT"
            :url "https://opensource.org/licenses/MIT"}

  :main strategify.core

  :dependencies [[org.clojure/clojure "1.11.1"]
                 [org.clojure/core.logic "1.0.0"]
                 [org.clojure/core.async "1.6.681"]
                 [cheshire "5.12.0"]
                 [org.clojure/data.csv "1.0.1"]]

  :profiles {:dev {:dependencies [[cider/cider-nrepl "0.28.6"]]}

             :uberjar {:aot [strategify.core]
                     :uberjar-name "strategify.jar"}}

  :aliases {"test-all" ["exec" "-m" "strategify.core/test-all"]})