## Authors
* James Hongyi Zeng (hyzeng_at_stanford.edu)
* Peyman Kazemian (kazemian_at_stanford.edu)

## What is ATPG?
ATPG stands for "Automatic Test Packet Generation". It is a framework to formally test the correctness of a network by generating a test suite against the network configuration

ATPG reads router configurations and generates a device-independent model. The model is used to generate a minimum set of test packets to (minimally) exercise every link in the network or (maximally) exercise every rule in the network. Test packets are sent periodically and detected failures trigger a separate mechanism
to localize the fault. ATPG can detect both functional (e.g., incorrect firewall rule) and performance problems (e.g., congested queue). ATPG complements but goes beyond earlier work in static checking (which cannot detect liveness or performance faults) or fault localization (which only localize faults given liveness results).

## What can I find from this repository?
This git repository hosts all the necessary code to run ATPG against Cisco or Juniper router configuration files. To demonstrate the usage of ATPG, we include two example networks - a Stanford backbone network captured on June 2011, and a Internet2 backbone captured on March 2012. You are welcome to try out your own network configurations.

## Reproduce our results
Our results are reported in our CoNEXT 2012 paper (to appear). We try hard to enable others to reproduce our results. The evaluation part of our paper is divided into two portions

* Offline evaluation
An offline evaluation part calculates the number of test packets needed in various scenarios. The main results are reported in Table 5 and Figure 8 of our paper. Please follow the [[Offline evaluation]] page to reproduce our results.

* Online evaluation (Mini-Stanford)
For online evaluation part (Figure 9 and 10), we use Mininet to emulate the behavior of Stanford network. We develop a set of tools called [[Mini-Stanford]]. Visit the wiki page for detailed instructions.

## How can I use ATPG in my own network?
ATPG is still in early development phase.

At this stage, the easiest way to try it out in your own network is to first understand how it works and what the results mean, with the two built-in examples - Stanford backbone (Cisco-based) and Internet2  backbone (Juniper based). Then you may replace the Stanford or Internet2 data with your own network configurations. During this process, the following files may need to be replicated and modified accordingly

```
utils/generate_stanford_backbone_tf.py
utils/load_stanford_backbone.py
atpg_stanford.py
```

