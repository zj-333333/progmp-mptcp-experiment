# 10102 Language and Concept Overview

The domain-specific programming model relies on the following abstractions, which are provided as entities in the language. Most entities, such as the congestion control values and round-trip times, have a direct counterpart in the Linux Kernel network stack. The following list is not complete yet. We will update the list soon.

Each scheduler starts with the `SCHEDULER` keyword followed by its name and a terminating `;`.

```
SCHEDULER myFirstScheduler;
```

### Types

**ProgMP** uses an implicit type system. In most cases, the developer does not have to care about the underlying types. The following underlying types are used:

- Boolean
- Unsigned Integer
- String
- Subflow
- Subflow List
- Packet
- Packet Queue

### Statements

**ProgMP** supports the following statements:

#### DROP

Drops a packet. Be careful to not drop packets which were not sent so far.

```
DROP(Q.POP());
```

#### FOREACH

Loops over all items inside a list.

```
FOREACH(VAR sbf IN SUBFLOWS) {
  /* Do something */
}
```

#### IF

Executes code depending on a condition. The else branch is optional. Note that a condition which evaluates to `NULL` is treated as `FALSE`.

```
IF (SUBFLOWS.COUNT == 1) {
  PRINT("Exactly 1 subflow\n");
} ELSE {
  PRINT("More than 1 subflow\n");
}
```

#### PRINT

Print a message to the kernel console with an optional parameter (no lists supported as parameter). You may read the output using `dmesg`. Note that print statements have a strong impact on the performance and should only be used for debugging purposes.

```
PRINT("Hello world!\n");
PRINT("We have %d subflows.\n", SUBFLOWS.COUNT);
```

#### RETURN

Stops the execution of the scheduler.

```
RETURN;
```

#### SET

Sets a register to a value. If `value` is `NULL`, the register is not changed.

```
SET(R1, 42);
```

#### VAR

Declares a new variable. Variables can only be assigned once per scheduler execution (single assignment) and have an implicit type.

```
VAR x = 42;
VAR sbfs = SUBFLOWS.FILTER(sbf => sbf.CWND > 20);
```

#### VOID

Does nothing, but accepts a parameter. The parameter is evaluated (i.e., side effects might be triggered) but the result will be ignored. This statement is only used for measurements!

```
VOID(5+9)
```

### Built-in variables

**ProgMP** provides the following build-in variables:

#### Q

Returns the sending queue packet list.

```
Q.TOP
```

#### QU

Returns the unacknowledged packet list.

```
QU.TOP
```

#### RQ

Returns the retransmission queue packet list.

#### CURRENT_TIME_MS

Returns the current time in milliseconds.

```
CURRENT_TIME_MS
```

#### R1 - R6

Returns the value of the register with the given number. Registers are integer variables that keep their values across scheduler executions. **ProgMP** provides a fixed set of 6 registers to limit memory consumption.

```
PRINT("R1 has the value %d.\n", R1);
```

#### RANDOM

Returns a random integer value.

#### SUBFLOWS

Returns the list of currently active subflows.

```
PRINT("Number of subflows is %d", SUBFLOWS.COUNT)
```

### Packet Properties

Packets are chosen based on Q, QU or RQ. Each packet has the following properties.

#### SENT_ON(subflow)

Returns `TRUE` if the packet was already sent on the given subflow.

```
Q.TOP.SENT_ON(SUBFLOWS.MIN(sbf => sbf.RTT))
```

#### USER

Returns the user integer value of the packet, e.g., as set by the [extended API](https://progmp.net/#API).

```
PRINT("The top packet has %d as user property", Q.TOP.USER)
```

#### SEQ

Returns the sequence number of the packet.

```
PRINT("The top packet has the sequence number %d", Q.TOP.SEQ)
```

#### LENGTH

Returns the length of the packet.

```
PRINT("The top packet has a length of %d", Q.TOP.LENGTH)
```

#### PSH

Returns if the `PUSH` flag of the packet is set.

```
IF(Q.TOP.PSH) { PRINT("The top packet has a set PUSH flag"); }
```

### Packet Queue Properties

Each packet queue has the following properties.

#### COUNT

Returns the number of packets in the list.

```
Q.COUNT
```

#### EMPTY

Returns `TRUE` if the packet list is empty.

#### FILTER

Returns a list with those packets for which the given condition evaluated to `TRUE`.

```
VAR packetsToSend = Q.FILTER(s => !s.SENT_ON(SUBFLOWS.GET(0)));
```

#### POP

Removes the first packet from the packet list and returns it. This is not possible on QU or a queue resulting from a `FILTER` expression of QU. Packets retained by `POP` have to be pushed or dropped explicitly. In particular, `POP` must not be used in conditions. `POP` requires two brackets, as shown in the example, to indicate that it causes side effects.

```
SUBFLOWS.GET(0).PUSH(Q.POP())
```

#### TOP

Returns the first packet of the packet list without modifying the underlying list.

```
SUBFLOWS.GET(0).PUSH(Q.TOP)
```

#### GET(

Returns the packet with the given index. If the index exceeds the number of packets in the queue, `NULL` is returned.

```
QU.GET(2)
```

### Subflow Properties

#### CWND

Returns the congestion window value of the subflow.

#### HAS_WINDOW_FOR(packet)

Returns `TRUE` if the subflow has sufficient flow control window to send the given packet.

```
IF(SUBFLOW.GET(0).HAS_WINDOW_FOR(Q.TOP)) {
...
```

#### ID

Returns the unqiue identifier of the subflow.

```
PRINT("Subflow %d has the minimum round-trip-time.", SUBFLOWS.MIN(sbf => sbf.RTT).ID)
```

#### IS_BACKUP

Returns `TRUE` if the subflow is marked as backup.

#### LOST_SKBS

Returns the number of lost packets of the subflow.

#### RTT

Returns the round-trip time of the subflow.

#### RTT_VAR

Returns the variance of the round-trip time of the subflow.

#### SKBS_IN_FLIGHT

Returns the number of packets of the subflow that are in flight.

#### QUEUED

Returns the number of packets of the subflow that are queued.

#### USER

Returns the user specified subflow property.

#### SET_USER

Sets the user specified subflow property.

```
SUBFLOWS.MIN(sbf => sbf.RTT).SET_USER(5)
```

### Subflow List Properties

#### COUNT

Returns the number of subflows in the list.

#### EMPTY

Returns `TRUE` if the subflow list is empty.

#### FILTER

Returns a list with those subflows for which the given condition evaluated to `TRUE`.

```
VAR sbfs_with_small_rtt = SUBFLOWS.FILTER(s => s.RTT < 100);
```

#### GET

Returns the subflow with the given index. If the index exceeds the number of subflows in the list, `NULL` is returned. Check [here](https://progmp.net/#NULL) for more details regarding `NULL` handling.

#### MAX

Returns the subflow of the list for which the given condition evaluates to the greatest value. Subflows for which the condition evaluates to `NULL` are ignored. Check [here](https://progmp.net/#NULL) for more details regarding `NULL` handling.

If multiple subflows have the same, greatest value, only a single subflow is returned. In this case, it is not specified which subflow is returned. It is also not guaranteed that consecutive calls return the same subflow.

```
VAR sbfWithGreatestRtt = SUBFLOWS.MAX(sbf => sbf.RTT);
```

#### MIN

Returns the subflow of the list for which the given condition evaluates to the smallest value. Subflows for which the condition evaluates to `NULL` are ignored. Check [here](https://progmp.net/#NULL) for more details regarding `NULL` handling.

If multiple subflows have the same, minimum value, only a single subflow is return. In this case, it is not specified which subflow is returned, neither that consecutive calls return the same subflow.

```
VAR sbfWithSmallestRtt = SUBFLOWS.MIN(s => s.RTT);
```

#### SUM

Returns the sum of the expression evaluated over all subflows in the list.

```
VAR rtt_sum = SUBFLOWS.SUM(s => s.RTT);
```

### Operators

Values can be combined using comparison and arithmetic operators:

- `==` Compares     two integer values and returns `TRUE` if     they are equal.
- `==     NULL` Returns `TRUE` if a value of any type     is `NULL`.
- `!=` Compares     two integer values and returns `TRUE` if     they are unequal.
- `!=     NULL` Returns `TRUE` if a value of any type is     not `NULL`.
- `<` Compares     two integer values and returns `TRUE` if     the first is less than the second one.
- `<=` Compares     two integer values and returns `TRUE` if     the first is less than or equal the second one.
- `>` Compares     two integer values and returns `TRUE` if     the first is greater than the second one.
- `>=` Compares     two integer values and returns `TRUE` if     the first is greater than or equal the second one.
- `+` Adds     two integer values.
- `-` Subtracts     one integer value from another.
- `*` Multiplies     two integer values.
- `/` Divides     one integer value by another. Returns `NULL` if     the right value is 0.
- `%` Returns     the remainder of a division. Returns `NULL` if     the right value is 0.
- `AND` Performs     a logical AND operation on two boolean values. The second operand is not     evaluated if the first one evaluates to `FALSE`.
- `OR` Performs     a logical OR operation on two boolean values. The second operand is not     evaluated if the first one evaluates to `TRUE`.
- `!` Performs     a logical NOT operation on a boolean value.

### NULL handling

**ProgMP** handles `NULL` values gracefully and well-defined. In a boolean expression with `AND` or `OR`, `NULL` behaves like `FALSE`. All other expressions which contains `NULL` evaluate to `NULL`, e.g., `5 + NULL` evaluates to `NULL`, `NULL == FALSE` evaluates to `FALSE`, and `! NULL` evaluates to `NULL`. Early prototypes of **ProgMP** tried to avoid `NULL`. However, we found that schedulers became more complex and difficult to express without `NULL`.

A statement that uses a value as parameter that evaluates to `NULL` is not executed.

```
SUBFLOWS.GET(0).PUSH(Q.FILTER(s => FALSE).POP());
```

A statement that operates on a value that evaluates to `NULL` is not executed. This avoids, e.g., to accidentally remove a packet from Q in case a complex filter statement evaluates to `FALSE`.

```
SUBFLOWS.FILTER(sbf => FALSE).PUSH(Q.POP());
```

 
