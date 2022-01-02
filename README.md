# Robot Archery

I recently found out that Jane Street put out monthly [puzzles](https://www.janestreet.com/puzzles/) on their website. Having a bit of time to kill between 2021 Christmas and New Years, I thought I'd have a go at their December [Robot Archery challenge](https://www.janestreet.com/puzzles/robot-archery-index/).

## TLDR

Probability of Darrin winning = 0.1834376509

## Decoding the puzzle

The puzzle mentions that each robot is "equally skilled", and that each is equally likely to hit "any region R on the target". To me this says 2 things:

1. The robots' arrows are distributed uniformly in 2D space.
2. Each robot has the same cumulative distribution ![p(x)](https://latex.codecogs.com/svg.image?p(x)) of getting an arrow within ![x](https://latex.codecogs.com/svg.image?x) of the bullseye.
   
## Keeping it simple

With 4 robots, things quickly become complicated. Not only can the archery competition go on infinitely, but robots can drop out, creating a branching infinite set of unique matches. Faced with this, I decided that the easiest thing would be to solve the puzzle for 2 robots first and then generalize upwards to 4. 

## Monte Carlo

I now wanted to get a rough idea of the answer. To do this, I simulated the archery competition 100,000,000 times,
keeping a record of which robot won each.

### Implementation

I decided to write the [code](/java/MonteCarloArchery.java) in Java because I wanted to parallelize these simulations, and I much prefer Java's concurrency features to, say, Python's.

To generate hits evenly distributed in 2D space, I followed this
[StackOverflow answer](https://stackoverflow.com/a/50746409). The angle of the hit doesn't matter, so we just need to
generate the radius via `sqrt(random())`.

I found that running simulations of batches >= 10000 improved performance immensely. This is likely due to reduced
overhead associated with threads having to acquire a new task each time they finish one.

The results were as follows (Here `P(0)` is the probability of the first robot winning):

```
P(0): 0.6321684400
P(1): 0.3678315600
Took: 9.86s
```

### Limitations

A Monte Carlo approach's accuracy is proportional to ![\sqrt(n)](https://latex.codecogs.com/svg.image?\sqrt{n}) where n is the number of simulations performed. This means that, with my 100,000,000 simulations, I could only expect my answer to be correct to a measly 4 decimal places.

I needed a solution with much better numerical convergence. However, at least I now had a rough idea of the correct answer to test my future solutions against.

## The rabbit hole

My next instinct was to attempt to derive a solution by deriving and using the radial cumulative distribution function ![p(x)](https://latex.codecogs.com/svg.image?p(x)) mentioned above. This Way Madness Lies. After a few hours of integration and infinite sums, I decided to take a step back...

## A paradigm shift

In the 2 robot scenario, what's the probability of robot 1 winning on their first shot? The answer is zero, because it's impossible for one of the robots to win on their own shot. Similarly, robot 1 cannot win on shot 3, shot 5, etc.

Now, what's the probability of robot 1 winning on the 2nd shot of the game (i.e. robot 2's)?

Let's say that, rather than the robots taking turns to shoot the 1st and 2nd shots, they both shoot at the same time. In this scenario, robot 1 has a 50% chance of winning outright. This is because both robots are equally skilled, so there's a 50% chance shot 1 lands inside shot 2, and a 50% chance it lands outside.

If we can do a similar analysis for shots 4, 6, 8, etc... then we can calculate the chance of robot 1 winning as the infinite sum of the probability that it wins on each of these shots.

### Combinations to the rescue

Let's start with shot 3. Just like above, let's not worry about *when* the shots were taken, just about which outcomes cause robot 2 to win.

Let's imagine we're looking at the target which has 3 arrows in it. The arrows can be ordered by their closeness to the bullseye. We know there are 3! possible orderings, but which of these orderings mean that robot 2 won **on this shot**?

> ℹ️ From here on, I'll be using sequences of numbers to describe the outcomes of archery matches. These sequences represent the **spatial** ordering of the numbers, with the first element being the furthest from the bullseye. For example, the sequence `1243` means that the 1st shot was furthest away, followed by the 2nd, and 4th. The 3rd shot which was the closest to the bullseye.

```
123     no
132     yes!
213     no, because this means that robot 1 won on shot 2
231     no, because this means that robot 1 won on shot 2
312     yes!
321     no, because this means that robot 1 won on shot 2
```

2/6 of these orderings cause robot 2 to win on shot 3, so we can say that there's a 1/3 chance! In fact, we can identify the orderings as **those where all numbers are in order except the final one**.

For example, the orderings which cause robot 1 to win on shot 4 are:

```
1243
1423
4123
```

Notice that we've just taken `1234` and moved the `4` backwards 3 times. We can therefore generalize and say that the
probability of a robot winning on shot `s` is ![(s-1)/s!](https://latex.codecogs.com/svg.image?(s-1)/s!).

We now have an infinite sum for robot 1:

![infinite sum 1](https://latex.codecogs.com/svg.image?\frac{1}{2!}+\frac{3}{4!}+\frac{5}{6!}+...)

![infinite sum 2](https://latex.codecogs.com/svg.image?=1-\frac{1}{2!}+\frac{1}{3!}-\frac{1}{4!}+\frac{1}{5!}-\frac{1}{6!}+...)

![infinite sum 3](https://latex.codecogs.com/svg.image?=\sum_{n=1}^{\infty}\frac{(-1)^{n+1}}{n!})

This can be [plugged into Wolfram Alpha](https://www.wolframalpha.com/input/?i=sum+%28-1%29%5E%28n%2B1%29%2Fn%21%2C+n%3D1+to+infinity)
to get an answer of ![(e-1)/e](https://latex.codecogs.com/svg.image?(e-1)/e), or 0.63212, which matches what we got from
our Monte Carlo simulation!

## More players

Let's push the above analogy further. This time, imagine that the entire match is played by 1 of the robots (they're all equally skilled after all). This robot shoots at the target until it has failed to get closer to the bullseye `n-1` times, at which point the match ends. The winner is then decided by the final sequence of shots.

For example, let's say the final sequence was `1243576` in a 3 robot match. Then the winner is decided like so:

```
shot    robot at stake  robot went out?
1       1               no
2       2               no
3       3               no
4       1               yes
5       2               no
6       3               no
7       2               yes

final winner: robot 3
```

Note that not all sequences of size `s` count as a match that was won on round `s`. For example, `2314567` doesn't represents a match that was won on round 7, because after round 3, robot 1 has won.

It's important to note that each valid sequence is **equally likely to occur**. Therefore if we can generate all valid sequences of size `s`, and apply the method of finding the winner as shown above to each, we should be able to find the probability of each robot winning on any given round. We can then sum these winning probabilities for each robot until they converge!

### What makes a sequence valid?

In a game with `n` players, exactly `n-1` shots need to fail to get closer to the bullseye. This means our sequence needs to have exactly `n-1` numbers out of order, and the rest in order. Also, one of these numbers needs to be the final number in the sequence.

1. Take an ordered sequence: `1234567`
2. Remove `n-1` numbers (one of which must be the final number): `12346`, with `5` and `7` removed
3. Add each removed number back, ensuring that any removed number `r` is placed **before** `r-1` (e.g. 5 must come before 4): `1243746`

So using the generative method above, how many ways are there of re-inserting the numbers to create a unique sequence? If we decide to remove the numbers ![removed numbers](https://latex.codecogs.com/svg.image?r_1,r_2,...r_n), we can generate ![product](https://latex.codecogs.com/svg.image?C=(r_1-1)\times(r_2-1)\times...\times(r_{n-1}-1)) winning sequences (or ![product](https://latex.codecogs.com/svg.image?r_1\times{r_2}\times...\times{r_{n-1}}) if we start our sequences at 0 rather than 1).

More importantly, for any given set of removed numbers, the winner **will be the same** for all `C` generated sequences. If we notice that the removed numbers are the **missed shots**, the winner-deciding algorithm above still applies. We'll call a set of removed numbers a **missed shot set**.

### The solution

Considering there are `s!` possible sequences of length `s`, we now have a viable way of solving the problem. The implementation will look something like:

```
n = number of players

for sequence length (s) in 1..infinity:
    generate all possible sets of n-1 missed shots
    for each missed shot set:
        find the associated winner
        calculate the associated number of generated sequences (C)
        add C to winner's total for this sequence length (total_C)
    for each robot:
        probability of winning this round = total_C / s!
```

The Python code for this was relatively simple and can be found [here](/python/combination_counting_archery.py). The initial output (below) looked promising. Each column is for a different robot (`P(0)` is robot 1 and so on). Each row is a more accurate approximation of the probability of each robot winning.

```
s             P(0)            P(1)            P(2)            P(3)
1             0.0000000000    0.0000000000    0.0000000000    0.0000000000
2             0.0000000000    0.0000000000    0.0000000000    0.0000000000
3             0.2500000000    0.0000000000    0.0000000000    0.0000000000
4             0.2500000000    0.2000000000    0.1000000000    0.0666666667
5             0.3263888889    0.2000000000    0.1833333333    0.1500000000
6             0.3621031746    0.2309523810    0.1916666667    0.1761904762
7             0.3692212302    0.2403273810    0.2008680556    0.1808779762
8             0.3706762566    0.2418264991    0.2028742284    0.1830164242
9             0.3710879630    0.2421166777    0.2031619268    0.1833810075
10            0.3711450818    0.2421800595    0.2032110289    0.1834293581
11            0.3711522007    0.2421875689    0.2032195487    0.1834365230
12            0.3711531142    0.2421884419    0.2032204545    0.1834375405
13            0.3711532238    0.2421885412    0.2032205510    0.1834376402
14            0.3711532338    0.2421885516    0.2032205607    0.1834376499
15            0.3711532347    0.2421885525    0.2032205617    0.1834376508
16            0.3711532348    0.2421885526    0.2032205617    0.1834376509
17            0.3711532348    0.2421885526    0.2032205617    0.1834376509
18            0.3711532348    0.2421885526    0.2032205617    0.1834376509
19            0.3711532348    0.2421885526    0.2032205617    0.1834376509
20            0.3711532348    0.2421885526    0.2032205617    0.1834376509
```

If all's gone well, the Monte Carlo simulation should produce roughly similar results...

```
P(0): 0.3711941700
P(1): 0.2420640000
P(2): 0.2032807600
P(3): 0.1834610700
Took: 19.9s 
```

...which it does!