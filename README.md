# Robot Archery

https://www.janestreet.com/puzzles/current-puzzle/

## TLDR

## Decoding the puzzle

The puzzle mentions that each robot is "equally skilled", and that each is equally likely to hit "any region R on the
target". To me this says 2 things:

1. The robots arrows are distributed uniformly in 2D space.
2. Each robot has the same cumulative distribution ![p(x)](https://latex.codecogs.com/svg.image?p(x)) of getting an
   arrow within ![x](https://latex.codecogs.com/svg.image?x) of the bullseye.
   
## Keeping it simple

With 4 robots, things quickly become complicated. Not only can the archery competition go on infinitely, but robots
can drop out, creating a branching infinite set of unique matches. Faced with this, I decided that the easiest thing
would be to solve the puzzle for 2 robots first and then generalize upwards to 4. 

## Monte Carlo

I now wanted to get a rough idea of the answer. To do this, I simulated the archery competition 100,000,000 times,
keeping a record of which robot won each.

### Implementation

I decided to write the [code](/RobotArchery.java) in Java because I wanted to
parallelize these simulations, and I much prefer Java's concurrency features to, say, Python's.

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

A Monte Carlo approach's accuracy is proportional to ![\sqrt(n)](https://latex.codecogs.com/svg.image?\sqrt{n}) where
n is the number of simulations performed. This means that, with my 100,000,000 simulations, I could only expect my 
answer to be correct to a measly 4 decimal places.

I needed a solution with much better numerical convergence. However, at least I now had a rough idea of the correct
answer to test my future solutions against.

## The rabbit hole

My next instinct was to attempt to derive a solution by deriving and using the radial cumulative distribution function
![p(x)](https://latex.codecogs.com/svg.image?p(x)) mentioned above. This Way Madness Lies. After a few hours of
integration and infinite sums, I decided to take a step back...

## A paradigm shift

In the 2 robot scenario, what's the probability of robot 1 winning on their first shot? The answer is zero, because
it's impossible for one of the robots to win on their own shot. Similarly, robot 1 cannot win on shot 3, shot 5, etc.

Now, what's the probability of robot 1 winning on the 2nd shot of the game (i.e. robot 2's)?

Let's say that, rather than the robots taking turns to shoot the 1st and 2nd shots, they both shoot at the same time. In
this scenario, robot 1 has a 50% chance of winning outright. This is because both robots are equally skilled, so there's
a 50% chance shot 1 lands inside shot 2, and a 50% chance it lands outside.

If we can do a similar analysis for shots 4, 6, 8, etc... then we can calculate the chance of robot 1 winning as the
infinite sum of the probability that it wins on each of these shots.

### Combinations to the rescue

Let's start with shot 3. Just like above, let's not worry about *when* the shots were taken, just about which outcomes
cause robot 2 to win.

Let's imagine we're looking at the target which has 3 arrows in it. The arrows can be ordered by their closeness to the
bullseye. We know there are 3! possible orderings, but which of these orderings mean that robot 2 won **on this shot**?

```
123     no
132     yes!
213     no, because this means that robot 1 won on shot 2
231     no, because this means that robot 1 won on shot 2
312     yes!
321     no, because this means that robot 1 won on shot 2
```

2/6 of these orderings cause robot 2 to win on shot 3, so we can say that there's a 1/3 chance! In fact, we can identify
the orderings as **those where all numbers are in order except the final one**.

For example, the orderings which cause robot 1 to win on shot 4 are:

```
1243
1423
4123
```

Notice that we've just taken `1234` and moved the `4` backwards 3 times. We can therefore generalize and say that the
probability of a robot winning on shot `n` is ![(n-1)/n!](https://latex.codecogs.com/svg.image?(n-1)/n!).

We now have an infinite sum for robot 1:

![infinite sum 1](https://latex.codecogs.com/svg.image?\frac{1}{2!}+\frac{3}{4!}+\frac{5}{6!}+...)

![infinite sum 2](https://latex.codecogs.com/svg.image?=1-\frac{1}{2!}+\frac{1}{3!}-\frac{1}{4!}+\frac{1}{5!}-\frac{1}{6!}+...)

![infinite sum 3](https://latex.codecogs.com/svg.image?=\sum_{n=1}^{\infty}\frac{(-1)^{n+1}}{n!})

This can be [plugged into Wolfram Alpha](https://www.wolframalpha.com/input/?i=sum+%28-1%29%5E%28n%2B1%29%2Fn%21%2C+n%3D1+to+infinity)
to get an answer of ![(e-1)/e](https://latex.codecogs.com/svg.image?(e-1)/e), or 6.63212, which matches what we got from
our Monte Carlo simulation!

## More players