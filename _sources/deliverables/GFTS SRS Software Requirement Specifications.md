# GFTS SRS Software Requirement Specifications

## Introduction

This document describes the software requirements specifications for the Global Fish Tracking Software (GFTS) DestinE Platform use case. We will describe both the functional and non-functional requirements on the GFTS system.

## Requirements

The following sections list the requirements for the fish track modelling environment and the decision support tool components.

### Modelling environment

The pangeo-fish modelling environment allows researchers to reconstruct fish tracks from the biologging data they collect.

---

**ID** **Requirement** **Description**

---

R101 Scalable Jupyter-Hub environment A Jupyter Hub environment is deployed in a scalable cloud architecture, it will be the basis for running fish track reconstruction

R102 Access Copernicus Marine Data The Copernicus Marine data is accessible in the Jupyter Hub environment for analysis

R103 Seabass biologging data The biologging data for Seabass is integrated and ready for analysis

R104 Pangeo-fish software The pangeo-fish software is installed and ready for analysis

R105 Fish track model output Fish presence probability distribution and most probable fish tracks

R106 Pollock biologging data The biologging data for Pollock is integrated and ready for analysis

---

### Decision Support Tool

The Decision Support Tool allows people to explore historic fish tracks and calculate future ocean conditions for the population.

---

**ID** **Requirement** **Description**

---

R201 Select existing tracks Users can select the fish tracks for a fish species generated within the context of this project

R202 Explore movement Users will be able to explore the fish tracks in the browser, and better understand behavioural patterns of the population.

R203 Climate DT data is available The Climate Adaptation Digital Twin is essential input for calculating the exposure of the fish tracks to future scenarios.

R204 Select Climate Change scenario Before calculating the future exposure of the population, people will be able to customise some of the underlying assumptions, such as different Climate Change scenarios. The scenarios would correspond to the data available in the Climate Adaptation Digital Twin.

R205 Explore future exposure People will be able to explore the future ocean conditions that the species is exposed to based on the available climate scenarios.

R206 Explore species groups by season Users will be able to explore the most probable fish habitat on a species level by season.

---
