import stormpy
import payntbind

import paynt.family.family
import paynt.models.models

import math
import itertools

import logging
logger = logging.getLogger(__name__)


class Quotient:

    # if True, expected visits will not be computed for hole scoring
    disable_expected_visits = False

    # label associated with un-labelled choices
    EMPTY_LABEL = "__no_label__"

    @staticmethod
    def make_vector_defined(vector):
        vector_noinf = [ value if value != math.inf else 0 for value in vector]
        default_value = sum(vector_noinf) / len(vector)
        vector_valid = [ value if value != math.inf else default_value for value in vector]
        return vector_valid

    def __init__(self, quotient_mdp = None, family = None, coloring = None, specification = None):

        # colored qoutient MDP for the super-family
        self.quotient_mdp = quotient_mdp
        self.family = family
        self.coloring = coloring
        self.specification = specification

        # builder options
        self.subsystem_builder_options = stormpy.SubsystemBuilderOptions()
        self.subsystem_builder_options.build_state_mapping = True
        self.subsystem_builder_options.build_action_mapping = True

        # for each choice of the quotient, a list of its state-destinations
        self.choice_destinations = None
        if self.quotient_mdp is not None:
            self.choice_destinations = payntbind.synthesis.computeChoiceDestinations(self.quotient_mdp)


    def export_result(self, dtmc):
        ''' to be overridden '''
        pass


    def restrict_mdp(self, mdp, choices):
        '''
        Restrict the quotient MDP to the selected actions.
        :param choices a bitvector of selected actions
        :return (1) the restricted model
        :return (2) sub- to full state mapping
        :return (3) sub- to full action mapping
        '''
        keep_unreachable_states = False # TODO investigate this
        all_states = stormpy.BitVector(mdp.nr_states, True)
        submodel_construction = stormpy.construct_submodel(
            mdp, all_states, choices, keep_unreachable_states, self.subsystem_builder_options
        )
        model = submodel_construction.model
        state_map = submodel_construction.new_to_old_state_mapping.copy()
        choice_map = submodel_construction.new_to_old_action_mapping.copy()
        return model,state_map,choice_map

    def restrict_quotient(self, choices):
        return self.restrict_mdp(self.quotient_mdp, choices)

    def build_from_choice_mask(self, choices):
        mdp,state_map,choice_map = self.restrict_quotient(choices)
        return paynt.models.models.SubMdp(mdp, state_map, choice_map)

    def build(self, family):
        ''' Construct the quotient MDP for the family. '''
        # select actions compatible with the family and restrict the quotient
        choices = self.coloring.selectCompatibleChoices(family.family)
        family.mdp = self.build_from_choice_mask(choices)
        family.selected_choices = choices
        family.mdp.family = family


    @staticmethod
    def mdp_to_dtmc(mdp):
        tm = mdp.transition_matrix
        tm.make_row_grouping_trivial()
        assert tm.nr_columns == tm.nr_rows, "expected transition matrix without non-trivial row groups"
        if mdp.is_exact:
            components = stormpy.storage.SparseExactModelComponents(tm, mdp.labeling, mdp.reward_models)
            dtmc = stormpy.storage.SparseExactDtmc(components)
            return dtmc
        else:
            components = stormpy.storage.SparseModelComponents(tm, mdp.labeling, mdp.reward_models)
            dtmc = stormpy.storage.SparseDtmc(components)
            return dtmc

    def build_assignment(self, family):
        assert family.size == 1, "expecting family of size 1"
        choices = self.coloring.selectCompatibleChoices(family.family)
        assert choices.number_of_set_bits() > 0
        mdp,state_map,choice_map = self.restrict_quotient(choices)
        model = Quotient.mdp_to_dtmc(mdp)
        return paynt.models.models.SubMdp(model,state_map,choice_map)

    def empty_scheduler(self):
        return [None] * self.quotient_mdp.nr_states

    def discard_unreachable_choices(self, state_to_choice):
        state_to_choice_reachable = self.empty_scheduler()
        state_visited = [False]*self.quotient_mdp.nr_states
        initial_state = list(self.quotient_mdp.initial_states)[0]
        state_visited[initial_state] = True
        state_queue = [initial_state]
        while state_queue:
            state = state_queue.pop()
            choice = state_to_choice[state]
            state_to_choice_reachable[state] = choice
            for dst in self.choice_destinations[choice]:
                if not state_visited[dst]:
                    state_visited[dst] = True
                    state_queue.append(dst)
        return state_to_choice_reachable

    def scheduler_to_state_to_choice(self, submdp, scheduler, discard_unreachable_choices=True):
        if submdp.model.is_exact:
            state_to_quotient_choice = payntbind.synthesis.schedulerToStateToGlobalChoiceExact(scheduler, submdp.model, submdp.quotient_choice_map)
        else:
            state_to_quotient_choice = payntbind.synthesis.schedulerToStateToGlobalChoice(scheduler, submdp.model, submdp.quotient_choice_map)
        state_to_choice = self.empty_scheduler()
        for state in range(submdp.model.nr_states):
            quotient_choice = state_to_quotient_choice[state]
            quotient_state = submdp.quotient_state_map[state]
            state_to_choice[quotient_state] = quotient_choice
        if discard_unreachable_choices:
            state_to_choice = self.discard_unreachable_choices(state_to_choice)
        return state_to_choice

    def state_to_choice_to_choices(self, state_to_choice):
        num_choices = self.quotient_mdp.nr_choices
        choices = stormpy.BitVector(num_choices,False)
        for choice in state_to_choice:
            if choice is not None and choice < num_choices:
                choices.set(choice,True)
        return choices

    def scheduler_selection(self, mdp, scheduler):
        ''' Get hole options involved in the scheduler selection. '''
        assert scheduler.memoryless and scheduler.deterministic
        state_to_choice = self.scheduler_to_state_to_choice(mdp, scheduler)
        choices = self.state_to_choice_to_choices(state_to_choice)
        hole_selection = self.coloring.collectHoleOptions(choices)
        return hole_selection


    def choice_values(self, mdp, prop, state_values):
        '''
        Get choice values after model checking MDP against a property.
        Value of choice c: s -> s' is computed as
        rew(c) + sum_s' [ P(s,c,s') * mc(s') ], where
        - rew(c) is the reward associated with choice (c)
        - P(s,c,s') is the probability of transitioning from s to s' under action c
        - mc(s') is the model checking result in state s'
        '''

        # multiply probability with model checking results
        if mdp.is_exact:
            choice_values = payntbind.synthesis.multiply_with_vector_exact(mdp.transition_matrix, state_values)
        else:
            choice_values = payntbind.synthesis.multiply_with_vector(mdp.transition_matrix, state_values)
        choice_values = Quotient.make_vector_defined(choice_values)

        # if the associated reward model has state-action rewards, then these must be added to choice values
        if prop.reward:
            reward_name = prop.formula.reward_name
            rm = mdp.reward_models.get(reward_name)
            assert rm.has_state_action_rewards
            choice_rewards = list(rm.state_action_rewards)
            assert mdp.nr_choices == len(choice_rewards)
            for choice in range(mdp.nr_choices):
                choice_values[choice] += choice_rewards[choice]

        return choice_values


    def compute_expected_visits(self, mdp, prop, choices):
        '''
        Compute expected number of visits in the states of DTMC induced by the shoices.
        '''
        if Quotient.disable_expected_visits:
            return [1]*self.quotient_mdp.nr_states

        # extract DTMC induced by this MDP-scheduler
        sub_mdp,state_map,_ = self.restrict_mdp(mdp, choices)
        dtmc = Quotient.mdp_to_dtmc(sub_mdp)
        dtmc_visits = paynt.verification.property.Property.compute_expected_visits(dtmc)

        # handle infinity- and zero-visits
        if prop.minimizing:
            dtmc_visits = Quotient.make_vector_defined(dtmc_visits)
        else:
            dtmc_visits = [ value if value != math.inf else 0 for value in dtmc_visits]

        # map vector of expected visits onto the state space of the quotient MDP
        expected_visits = [0] * mdp.nr_states
        for state in range(dtmc.nr_states):
            mdp_state = state_map[state]
            visits = dtmc_visits[state]
            expected_visits[mdp_state] = visits

        return expected_visits


    def estimate_scheduler_difference(self, mdp, quotient_choice_map, inconsistent_assignments, choice_values, expected_visits):
        hole_variance = payntbind.synthesis.computeInconsistentHoleVariance(
            self.family.family, mdp.nondeterministic_choice_indices, quotient_choice_map, choice_values,
            self.coloring, inconsistent_assignments, expected_visits)
        return hole_variance


    def scheduler_is_consistent(self, mdp, prop, result):
        '''
        Get hole assignment induced by this scheduler and fill undefined
        holes by some option from the design space of this mdp.
        :return hole assignment
        :return whether the scheduler is consistent
        '''
        if mdp.is_deterministic:
            selection = [[mdp.family.hole_options(hole)[0]] for hole in range(mdp.family.num_holes)]
            return selection, True

        # get qualitative scheduler selection, filter inconsistent assignments
        selection = self.scheduler_selection(mdp, result.scheduler)
        inconsistent_assignments = {hole:options for hole,options in enumerate(selection) if len(options) > 1 }
        scheduler_is_consistent = len(inconsistent_assignments) == 0
        for hole,options in enumerate(selection):
            if len(options) == 0:
                # if some hole options are not involved in the selection, we can fix an arbitrary value
                selection[hole] = [mdp.family.hole_options(hole)[0]]

        return selection, scheduler_is_consistent

    def scheduler_scores(self, mdp, prop, result, selection):
        inconsistent_assignments = {hole:options for hole,options in enumerate(selection) if len(options) > 1 }
        choice_values = self.choice_values(mdp.model, prop, result.get_values())
        choices = result.scheduler.compute_action_support(mdp.model.nondeterministic_choice_indices)
        expected_visits = self.compute_expected_visits(mdp.model, prop, choices)
        scores = self.estimate_scheduler_difference(mdp.model, mdp.quotient_choice_map, inconsistent_assignments, choice_values, expected_visits)
        return scores


    def suboptions_half(self, mdp, splitter):
        ''' Split options of a splitter into two halves. '''
        options = mdp.family.hole_options(splitter)
        half = len(options) // 2
        suboptions = [options[:half], options[half:]]
        return suboptions

    def suboptions_unique(self, mdp, splitter, used_options):
        ''' Distribute used options of a splitter into different suboptions. '''
        assert len(used_options) > 1
        suboptions = [[option] for option in used_options]
        index = 0
        for option in mdp.family.hole_options(splitter):
            if option in used_options:
                continue
            suboptions[index].append(option)
            index = (index + 1) % len(suboptions)
        return suboptions

    def suboptions_enumerate(self, mdp, splitter, used_options):
        assert len(used_options) > 1
        core_suboptions = [[option] for option in used_options]
        other_suboptions = [option for option in mdp.family.hole_options(splitter) if option not in used_options]
        return core_suboptions, other_suboptions

    def holes_with_max_score(self, hole_score):
        max_score = max(hole_score.values())
        with_max_score = [hole_index for hole_index in hole_score if hole_score[hole_index] == max_score]
        return with_max_score

    def split(self, family):

        mdp = family.mdp
        assert not mdp.is_deterministic

        # split family wrt last undecided result
        result = family.analysis_result.undecided_result()
        hole_assignments = result.primary_selection
        scores = self.scheduler_scores(mdp, result.prop, result.primary.result, result.primary_selection)
        if scores is None:
            scores = {hole:0 for hole in range(mdp.family.num_holes) if mdp.family.hole_num_options(hole) > 1}

        splitters = self.holes_with_max_score(scores)
        splitter = splitters[0]
        if len(hole_assignments[splitter]) > 1:
            core_suboptions,other_suboptions = self.suboptions_enumerate(mdp, splitter, hole_assignments[splitter])
        else:
            assert mdp.family.hole_num_options(splitter) > 1
            core_suboptions = self.suboptions_half(mdp, splitter)
            other_suboptions = []
        # print(mdp.family[splitter], core_suboptions, other_suboptions)

        if len(other_suboptions) == 0:
            suboptions = core_suboptions
        else:
            suboptions = [other_suboptions] + core_suboptions  # DFS solves core first

        # construct corresponding subfamilies
        parent_info = family.collect_parent_info(self.specification)
        subfamilies = family.split(splitter,suboptions)
        for subfamily in subfamilies:
            subfamily.add_parent_info(parent_info)
        return subfamilies


    def get_property(self):
        assert self.specification.num_properties == 1, "expecting a single property"
        return self.specification.all_properties()[0]

    @classmethod
    def identify_absorbing_states(cls, model):
        state_is_absorbing = [True] * model.nr_states
        tm = model.transition_matrix
        for state in range(model.nr_states):
            for choice in tm.get_rows_for_group(state):
                for entry in tm.get_row(choice):
                    if entry.column != state:
                        state_is_absorbing[state] = False
                        break
                if not state_is_absorbing[state]:
                    break
        return state_is_absorbing

    @classmethod
    def identify_states_with_actions(cls, model):
        ''' Get a mask of states having more than one action. '''
        state_has_actions = [None] * model.nr_states
        ndi = model.nondeterministic_choice_indices
        for state in range(model.nr_states):
            num_actions = ndi[state+1]-ndi[state]
            state_has_actions[state] = (num_actions>1)
        return state_has_actions

    def identify_target_states(self, model=None, prop=None):
        if model is None:
            model = self.quotient_mdp
        if prop is None:
            prop = self.get_property()
        if prop.is_discounted_reward:
            return stormpy.BitVector(model.nr_states,False)
        target_label = prop.get_target_label()
        return model.labeling.get_states(target_label)
