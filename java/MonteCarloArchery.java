import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedList;
import java.util.List;
import java.util.Map;
import java.util.Random;
import java.util.concurrent.Executors;
import java.util.concurrent.atomic.AtomicLong;
import java.util.stream.IntStream;
import java.util.stream.Stream;

import static java.lang.String.format;
import static java.lang.ThreadLocal.withInitial;
import static java.util.Collections.synchronizedList;
import static java.util.concurrent.TimeUnit.SECONDS;
import static java.util.function.UnaryOperator.identity;
import static java.util.stream.Collectors.*;

/**
 * @author harrydent
 */
public class MonteCarloArchery {

    public static void main(String[] args) {
        var tournament = new MonteCarloArchery(4, 100000000, 1000000, 24);
        tournament.playMatches();
    }

    private static final ThreadLocal<Random> RANDOM = withInitial(Random::new);
    private static final ThreadLocal<WinCounter> WIN_COUNTER = withInitial(WinCounter::new);
    private static final List<WinCounter> WIN_COUNTER_REGISTRY = synchronizedList(new ArrayList<>());

    private final long matches;
    private final long batchSize;
    private final int parallelism;
    private final List<Integer> initialPlayerList;

    public MonteCarloArchery(final int nPlayers,
                             final long matches,
                             final long batchSize,
                             final int parallelism) {
        this.matches = matches;
        this.batchSize = batchSize;
        this.parallelism = parallelism;

        // create a list that starts with the 2nd player e.g. [2, 3, 4, 1]
        this.initialPlayerList = IntStream.range(1, nPlayers).boxed().collect(toList());
        initialPlayerList.add(0);
    }

    public void playMatches() {
        var executorService = Executors.newFixedThreadPool(parallelism);

        var start = Instant.now();

        Stream.generate(MatchBatch::new)
            .limit(matches / batchSize)
            .forEach(executorService::execute);

        try {
            executorService.shutdown();
            executorService.awaitTermination(100, SECONDS);
        } catch (InterruptedException e) {
            throw new RuntimeException(e);
        }

        var reducedWinCounter = WIN_COUNTER_REGISTRY.stream()
            .reduce(WinCounter::merge)
            .orElseThrow();

        reducedWinCounter.check(matches);
        reducedWinCounter.print(matches);

        System.out.printf("Used %s shards%n", WIN_COUNTER_REGISTRY.size());

        var finish = Instant.now();
        var took = Duration.between(start, finish);
        System.out.printf("Took: %d.%ds%n", took.toSecondsPart(), took.toMillisPart());
    }

    class MatchBatch implements Runnable {

        @Override
        public void run() {
            Stream.generate(Match::new).limit(batchSize).forEach(Match::run);
        }
    }

    class Match implements Runnable {

        @Override
        public void run() {
            var random = RANDOM.get();
            var winCounter = WIN_COUNTER.get();
            var players = new LinkedList<>(initialPlayerList);
            var minRadius = Math.sqrt(random.nextDouble());

            while (players.size() > 1) {
                var currentPlayer = players.removeFirst();
                var nextRadius = Math.sqrt(random.nextDouble());
                if (nextRadius < minRadius) {
                    minRadius = nextRadius;
                    players.addLast(currentPlayer);
                }
            }

            // add to win counter
            winCounter.increment(players.pop());
        }
    }

    static class WinCounter {

        private final Map<Integer, AtomicLong> wins;

        public WinCounter() {
            this(new HashMap<>());
            WIN_COUNTER_REGISTRY.add(this);
        }

        private WinCounter(final Map<Integer, AtomicLong> wins) {
            this.wins = wins;
        }

        public void increment(final int n) {
            getCounter(n).incrementAndGet();
        }

        public WinCounter merge(final WinCounter other) {
            // set union of map keys
            var combinedKeys = Stream.concat(
                this.wins.keySet().stream(),
                other.wins.keySet().stream()
            ).collect(toSet());

            // sum up to new map
            var newWins = combinedKeys.stream()
                .collect(toMap(
                    identity(),
                    n -> new AtomicLong(getCounter(n).get() + other.getCounter(n).get())
                ));

            return new WinCounter(newWins);
        }

        public void check(long matches) {
            long totalWins = wins.values()
                .stream()
                .map(AtomicLong::get)
                .reduce(0L, Long::sum);

            if (totalWins != matches) {
                throw new RuntimeException(format(
                    "Total wins (%s) do not equal number of matches played (%s)",
                    totalWins, matches
                ));
            } else {
                System.out.println("Total wins is equal to number of matches");
            }
        }

        public void print(long matches) {
            wins.keySet()
                .stream()
                .sorted()
                .forEach(n -> System.out.printf("P(%s): %.10f%n", n, wins.get(n).get() / (double) matches));
        }

        private AtomicLong getCounter(final int n) {
            return wins.computeIfAbsent(n, k -> new AtomicLong());
        }
    }
}
