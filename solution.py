import argparse
import csv
import datetime
import math
import sys
from collections import defaultdict
from dataclasses import dataclass


class AgentPerformance:
    start_time: datetime.time
    end_time: datetime.time
    success_count: int
    success_amount: float

    def __init__(self):
        self.start_time = datetime.time.max
        self.end_time = datetime.time.min
        self.success_count = 0
        self.success_amount = 0

    def add_entry(self, time: datetime.time, success: bool, amount: float = 0):
        self.start_time = min(self.start_time, time)
        self.end_time = max(self.end_time, time)

        if success:
            self.success_count += 1
            self.success_amount += amount

    def work_hours(self) -> float:
        def to_seconds(time: datetime.time) -> int:
            return time.hour * 3600 + time.minute * 60 + time.second

        if self.start_time == self.end_time:
            return 1 / 3600

        return (to_seconds(self.end_time) - to_seconds(self.start_time)) / 3600


@dataclass
class PerformanceStatistic:
    success_count_per_hour: float = 0
    success_amount_per_hour: float = 0


class CampaignStatistic:
    average_performance: PerformanceStatistic
    best_count_agents: list[str]
    best_amount_agents: list[str]

    def __init__(self):
        self.average_performance = PerformanceStatistic()
        self.best_count_agents = []
        self.best_amount_agents = []


class ThresholdAgentsList:
    definite: list[str]
    potential: list[str]

    def __init__(self):
        self.definite = []
        self.potential = []


class DailyStatistic:
    campaign_statistics: dict[str, CampaignStatistic]
    underperforming_count_agents: ThresholdAgentsList
    underperforming_amount_agents: ThresholdAgentsList

    def __init__(self):
        self.campaign_statistics = {}
        self.underperforming_count_agents = ThresholdAgentsList()
        self.underperforming_amount_agents = ThresholdAgentsList()


def get_dates_from_file(file) -> set[datetime.date]:
    dict_reader = csv.DictReader(file)
    dates = set[datetime.date]()

    for row in dict_reader:
        dates.add(datetime.datetime.fromisoformat(row["CALLTIME"]).date())

    return dates

def get_field_set_from_file(file, field: str) -> set[str]:
    dict_reader = csv.DictReader(file)
    field_set = set[str]()

    for row in dict_reader:
        field_set.add(row[field])

    return field_set

def process_date(file, date: datetime.date) -> DailyStatistic:
    dict_reader = csv.DictReader(file)

    type agents_performance_dict = defaultdict[str, AgentPerformance]

    def get_agent_performance_dict() -> agents_performance_dict:
        return defaultdict(AgentPerformance)

    all_agents = set[str]()
    individual_performance = get_agent_performance_dict()
    campaign_performance = defaultdict[str, agents_performance_dict](get_agent_performance_dict)

    for row in dict_reader:
        all_agents.add(row["AGENT"])

        dt = datetime.datetime.fromisoformat(row["CALLTIME"])

        if dt.date() == date:
            success: bool = row["STATUS"] in ["SALE", "CCSALE", "CREDIT"]
            amount: float = float(row["AMOUNT"]) if row["AMOUNT"] else 0
            time = dt.time()

            individual_performance[row["AGENT"]].add_entry(time, success, amount)
            campaign_performance[row["CAMPAIGN"]][row["AGENT"]].add_entry(time, success, amount)

    statistic = DailyStatistic()

    for campaign, agents_performance in campaign_performance.items():
        statistic.campaign_statistics[campaign] = CampaignStatistic()

        total_count: int = 0
        total_amount: float = 0
        total_hours: float = 0
        best_performance = PerformanceStatistic()

        for performance in agents_performance.values():
            hours: float = performance.work_hours()
            average_performance = PerformanceStatistic(performance.success_count / hours, performance.success_amount / hours)

            total_count += performance.success_count
            total_amount += performance.success_amount
            total_hours += hours

            if average_performance.success_count_per_hour > best_performance.success_count_per_hour:
                best_performance.success_count_per_hour = average_performance.success_count_per_hour

            if average_performance.success_amount_per_hour > best_performance.success_amount_per_hour:
                best_performance.success_amount_per_hour = average_performance.success_amount_per_hour

        campaign_statistic: CampaignStatistic = statistic.campaign_statistics[campaign]

        campaign_statistic.average_performance.success_count_per_hour = total_count / total_hours
        campaign_statistic.average_performance.success_amount_per_hour = total_amount / total_hours

        for agent, performance in agents_performance.items():
            hours: float = performance.work_hours()
            average_performance = PerformanceStatistic(performance.success_count / hours, performance.success_amount / hours)

            if average_performance.success_count_per_hour == best_performance.success_count_per_hour:
                campaign_statistic.best_count_agents.append(agent)

            if average_performance.success_amount_per_hour == best_performance.success_amount_per_hour:
                campaign_statistic.best_amount_agents.append(agent)

    type agents_statistic_list = list[tuple[str, float]]

    agents_sorted_by_count_performance: agents_statistic_list = []
    agents_sorted_by_amount_performance: agents_statistic_list = []

    for agent in all_agents:
        performance: AgentPerformance = individual_performance.get(agent, AgentPerformance())

        hours: float = performance.work_hours()

        agents_sorted_by_count_performance.append((agent, performance.success_count / hours))
        agents_sorted_by_amount_performance.append((agent, performance.success_amount / hours))

    agents_sorted_by_count_performance.sort(key=lambda t: t[1])
    agents_sorted_by_amount_performance.sort(key=lambda t: t[1])

    def separate_list_by_position(agent_list: agents_statistic_list, position: int) -> ThresholdAgentsList:
        output_list = ThresholdAgentsList()
        end_position: int = len(agent_list)

        if position == 0:
            return output_list

        if position == end_position:
            output_list.definite = [s for s, _ in agent_list]
            return output_list

        lower_bound: int = position - 1
        upper_bound: int = position

        if agent_list[lower_bound][1] != agent_list[upper_bound][1]:
            output_list.definite = [s for s, _ in agent_list[:upper_bound]]
            return output_list

        while lower_bound > 0 and agent_list[lower_bound][1] == agent_list[lower_bound - 1][1]:
            lower_bound -= 1

        while upper_bound < end_position and agent_list[upper_bound - 1][1] == agent_list[upper_bound][1]:
            upper_bound += 1

        output_list.definite = [s for s, _ in agent_list[:lower_bound]]
        output_list.potential = [s for s, _ in agent_list[lower_bound:upper_bound]]

        return output_list

    target_position: int = math.floor(len(all_agents) * 0.2)

    statistic.underperforming_count_agents = separate_list_by_position(agents_sorted_by_count_performance, target_position)
    statistic.underperforming_amount_agents = separate_list_by_position(agents_sorted_by_amount_performance, target_position)

    return statistic

def display_daily_statistic(file, statistic: DailyStatistic):
    for campaign in sorted(statistic.campaign_statistics.keys()):
        campaign_statistic: CampaignStatistic = statistic.campaign_statistics[campaign]

        file.write(f"Campaign: {campaign}\n")
        file.write(f"\tAverage performance:\n")
        file.write(f"\t\t{campaign_statistic.average_performance.success_count_per_hour:.3f} number of sales per hour\n")
        file.write(f"\t\t{campaign_statistic.average_performance.success_amount_per_hour:.3f} amount sold per hour\n")

        if len(campaign_statistic.best_count_agents) == 0:
            file.write(f"\tNo best agents by number of sales per hour reported\n")
        elif len(campaign_statistic.best_count_agents) == 1:
            file.write(f"\tBest agent by number of sales per hour:\n")
            file.write(f"\t\t{campaign_statistic.best_count_agents[0]}\n")
        else:
            file.write(f"\tBest agents by number of sales per hour:\n")

            for agent in sorted(campaign_statistic.best_count_agents):
                file.write(f"\t\t{agent}\n")

        if len(campaign_statistic.best_amount_agents) == 0:
            file.write(f"\tNo best agents by amount sold per hour reported\n")
        elif len(campaign_statistic.best_amount_agents) == 1:
            file.write(f"\tBest agent by amount sold per hour:\n")
            file.write(f"\t\t{campaign_statistic.best_amount_agents[0]}\n")
        else:
            file.write(f"\tBest agents by amount sold per hour:\n")

            for agent in sorted(campaign_statistic.best_amount_agents):
                file.write(f"\t\t{agent}\n")

        file.write(f"\n")

    if len(statistic.underperforming_count_agents.definite) == 0:
        pass
        # file.write(f"No underperforming agents by number of sales per hour reported\n")
    elif len(statistic.underperforming_count_agents.definite) == 1:
        file.write(f"Underperforming agent by number of sales per hour:\n")
        file.write(f"\t{statistic.underperforming_count_agents.definite[0]}\n")
        file.write(f"\n")
    else:
        file.write(f"Underperforming agents by number of sales per hour (worst to best):\n")

        for agent in statistic.underperforming_count_agents.definite:
            file.write(f"\t{agent}\n")

        file.write(f"\n")

    if len(statistic.underperforming_count_agents.potential) == 0:
        pass
        # file.write(f"No potentially underperforming agents by number of sales per hour reported\n")
    elif len(statistic.underperforming_count_agents.potential) == 1:
        file.write(f"Potentially underperforming agent by number of sales per hour:\n")
        file.write(f"\t{statistic.underperforming_count_agents.potential[0]}\n")
        file.write(f"\n")
    else:
        file.write(f"Potentially underperforming agents by number of sales per hour:\n")

        for agent in sorted(statistic.underperforming_count_agents.potential):
            file.write(f"\t{agent}\n")

        file.write(f"\n")

    if len(statistic.underperforming_amount_agents.definite) == 0:
        pass
        # file.write(f"No underperforming agents by amount sold per hour reported\n")
    elif len(statistic.underperforming_amount_agents.definite) == 1:
        file.write(f"Underperforming agent by amount sold per hour:\n")
        file.write(f"\t{statistic.underperforming_amount_agents.definite[0]}\n")
        file.write(f"\n")
    else:
        file.write(f"Underperforming agents by amount sold per hour (worst to best):\n")

        for agent in statistic.underperforming_amount_agents.definite:
            file.write(f"\t{agent}\n")

        file.write(f"\n")

    if len(statistic.underperforming_amount_agents.potential) == 0:
        pass
        # file.write(f"No potentially underperforming agents by amount sold per hour reported\n")
    elif len(statistic.underperforming_amount_agents.potential) == 1:
        file.write(f"Potentially underperforming agent by amount sold per hour:\n")
        file.write(f"\t{statistic.underperforming_amount_agents.potential[0]}\n")
        file.write(f"\n")
    else:
        file.write(f"Potentially underperforming agents by amount sold per hour:\n")

        for agent in sorted(statistic.underperforming_amount_agents.potential):
            file.write(f"\t{agent}\n")

        file.write(f"\n")


def display_all_statistic(file, statistics: dict[datetime.date, DailyStatistic]):
    for date in sorted(statistics.keys()):
        statistic = statistics[date]

        file.write(f"PERFORMANCE REPORT - {date}\n")
        file.write('=' * 50)
        file.write(f"\n\n")

        display_daily_statistic(file, statistic)

        file.write('=' * 50)
        file.write(f"\n\n")


def main(input_filepath: str, output_filepath: str | None, print_to_console: bool):
    with open(input_filepath, 'r') as file:
        dates = get_dates_from_file(file)
        statistics: dict[datetime.date, DailyStatistic] = {}

        for date in dates:
            file.seek(0)

            statistics[date] = process_date(file, date)

    if output_filepath is not None:
        with open(output_filepath, 'w') as file:
            display_all_statistic(file, statistics)

    if print_to_console:
        display_all_statistic(sys.stdout, statistics)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="This script calculates average performance of campaigns and classifies agents by their individual performance from a provided CSV file.")
    parser.add_argument('--input', '-i', type=str, default='calls.csv',
                        help='Input CSV file path (default: calls.csv)')
    parser.add_argument('--output', '-o', type=str, default=None,
                        help='Output statistic file path (default: no file output)')
    parser.add_argument('--noprint', action='store_true',
                        help='Disable console output printing (default: print to console)')

    args = parser.parse_args()

    main(args.input, args.output, not args.noprint)