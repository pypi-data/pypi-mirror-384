# views.py
#
# Copyright (c) 2024 - 2025 Daniel Andrlik
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

import logging
from typing import TYPE_CHECKING, ClassVar

# from django.shortcuts import render
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import (
    ImproperlyConfigured,
    ObjectDoesNotExist,
    SuspiciousOperation,
)
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    FormView,
    ListView,
    TemplateView,
    UpdateView,
)
from django.views.generic.detail import SingleObjectMixin

if TYPE_CHECKING:
    from django.db.models import QuerySet

from podcast_analyzer.forms import AnalysisGroupForm, PersonMergeForm
from podcast_analyzer.models import AnalysisGroup, Episode, Person, Podcast

# Create your views here.

logger = logging.getLogger(__name__)


def messaging_enabled() -> bool:
    """Returns a bool representing if django's messages are enabled."""
    return "django.contrib.messages" in settings.INSTALLED_APPS


class SelectPrefetchRelatedMixin:
    """
    Adds two class variables:
        prefetch_related: list[str]
        select_related: list[str]
    If they are populated, it will use them in the queryset.
    """

    model = None
    queryset = None
    ordering = None
    prefetch_related: ClassVar[list[str] | None] = None
    select_related: ClassVar[list[str] | None] = None

    def get_queryset(self):
        if not self.queryset:
            if self.model:
                qs = self.model._default_manager.all()
            else:  # no cov
                msg = "View does not have a queryset or model defined!"
                raise ImproperlyConfigured(msg)
        else:
            qs = self.queryset
        if self.select_related:
            qs = qs.select_related(*self.select_related)
        if self.prefetch_related:
            qs = qs.prefetch_related(*self.prefetch_related)
        if self.ordering:
            if isinstance(self.ordering, str):
                qs = qs.order_by(self.ordering)  # no cov, we're just mimicking Django
            else:
                qs = qs.order_by(*self.ordering) # type: ignore
        return qs


class AppEntryView(LoginRequiredMixin, TemplateView):
    """The default view for the root of the application."""

    template_name = "podcast_analyzer/app_entry.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["podcast_count"] = Podcast.objects.count()
        context["people_count"] = Person.objects.count()
        context["analysis_group_count"] = AnalysisGroup.objects.count()
        context["episode_count"] = Episode.objects.count()
        return context


class PodcastListView(LoginRequiredMixin, SelectPrefetchRelatedMixin, ListView):
    """
    View all podcasts in a list.
    """

    model = Podcast
    ordering = ["title"]
    paginate_by = 25
    prefetch_related = ["episodes", "seasons", "analysis_group"]


class PodcastDetailView(LoginRequiredMixin, SelectPrefetchRelatedMixin, DetailView):
    """
    A view to see a given podcasts data.
    """

    model = Podcast
    pk_url_kwarg = "id"
    context_object_name = "podcast"
    prefetch_related = ["episodes", "seasons", "analysis_group"]


class PodcastCreateView(LoginRequiredMixin, CreateView):
    """
    Provides a form to create a podcast.
    """

    model = Podcast
    fields: ClassVar[list[str]] = ["title", "rss_feed"]  # type: ignore

    def form_invalid(self, form):
        if messaging_enabled():
            messages.error(
                self.request, _("Podcast could not be created. See errors below.")
            )
        return super().form_invalid(form)

    def get_success_url(self):
        if messaging_enabled():
            messages.success(self.request, _("Podcast created"))
        return super().get_success_url()


class PodcastUpdateView(LoginRequiredMixin, UpdateView):
    """
    View for updating a podcast record.
    """

    model = Podcast
    pk_url_kwarg = "id"
    fields: ClassVar[list[str]] = [  # type: ignore
        "title",
        "rss_feed",
        "site_url",
        "podcast_cover_art_url",
        "release_frequency",
        "probable_feed_host",
        "tags",
        "analysis_group",
    ]
    context_object_name = "podcast"

    def form_invalid(self, form):
        if messaging_enabled():
            messages.error(
                self.request, _("Podcast could not be updated. See errors below.")
            )
        return super().form_invalid(form)

    def get_success_url(self):
        if messaging_enabled():
            messages.success(self.request, _("Podcast updated"))
        return super().get_success_url()


class PodcastDeleteView(LoginRequiredMixin, SelectPrefetchRelatedMixin, DeleteView):
    """
    For deleting a podcast record.
    """

    model = Podcast
    context_object_name = "podcast"
    pk_url_kwarg = "id"
    object: Podcast
    prefetch_related = ["episodes", "seasons", "analysis_group"]

    def get_success_url(self):
        if messaging_enabled():
            messages.success(self.request, _("Podcast deleted"))
        return reverse_lazy("podcast_analyzer:podcast-list")


class PersonListView(LoginRequiredMixin, SelectPrefetchRelatedMixin, ListView):
    """View all people in a list"""

    model = Person
    pk_url_kwarg = "id"
    context_object_name = "people"
    paginate_by = 25
    ordering = ["name"]
    prefetch_related = ["hosted_episodes", "guest_appearances"]
    queryset = Person.objects.filter(merged_into__isnull=True)


class PersonDetailView(LoginRequiredMixin, SelectPrefetchRelatedMixin, DetailView):
    """View a specific person's details."""

    model = Person
    pk_url_kwarg = "id"
    context_object_name = "person"
    prefetch_related = ["hosted_episodes", "guest_appearances"]


class PersonUpdateView(LoginRequiredMixin, UpdateView):
    """Edit a given person's details."""

    model = Person
    fields: ClassVar[list[str]] = ["name", "url", "img_url"]
    context_object_name = "person"
    pk_url_kwarg = "id"

    def form_invalid(self, form):
        if messaging_enabled():
            messages.error(
                self.request, _("Person could not be updated. See errors below.")
            )
        return super().form_invalid(form)

    def get_success_url(self):
        if messaging_enabled():
            messages.success(self.request, _("Person updated"))
        return super().get_success_url()


class PersonDeleteView(LoginRequiredMixin, SelectPrefetchRelatedMixin, DeleteView):
    """Delete a person from the database."""

    model = Person
    pk_url_kwarg = "id"
    context_object_name = "person"
    prefetch_related = ["hosted_episodes", "guest_appearances"]
    select_related = ["merged_into"]
    object: Person

    def get_success_url(self):
        if messaging_enabled():
            messages.success(self.request, _("Person deleted"))
        return reverse_lazy("podcast_analyzer:person-list")


class PersonMergeListView(LoginRequiredMixin, SelectPrefetchRelatedMixin, ListView):
    """Show a list of people that this record could be merged with."""

    model = Person
    context_object_name = "merge_targets"
    prefetch_related = ["hosted_episodes", "guest_appearances"]
    select_related = ["merged_into"]
    template_name = "podcast_analyzer/person_merge_list.html"
    paginate_by = 20
    source_person: Person

    def get_queryset(self):
        person_id = self.kwargs.get("id", None)
        self.source_person = get_object_or_404(Person, pk=person_id)
        return Person.objects.filter(merged_into__isnull=True).exclude(
            id=self.source_person.id
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["person"] = self.source_person
        return context


class PersonMergeView(LoginRequiredMixin, SingleObjectMixin, FormView):
    """
    Show a confirmation screen so that the user can double-check what will be changed.
    Then perform the merge on a post.
    """

    model = Person
    pk_url_kwarg = "id"
    context_object_name = "source"
    destination: Person
    template_name = "podcast_analyzer/person_confirm_merge.html"
    form_class = PersonMergeForm
    object: Person

    def form_valid(self, form):
        source = form.cleaned_data.get("source_person")
        destination = form.cleaned_data.get("destination_person")
        if destination != self.destination or source != self.object:
            msg = "It looks like you are trying to tamper with the merge form."
            raise SuspiciousOperation(msg)
        records_updated = Person.merge_person(
            source_person=source, destination_person=destination
        )
        if messaging_enabled():
            messages.success(
                self.request,
                f"Merged successfully and updated {records_updated} related records.",
            )
        return HttpResponseRedirect(destination.get_absolute_url())

    def get_form_kwargs(self):
        if not hasattr(self, "object"):
            obj = self.get_object()
        else:
            obj = self.object
        self.initial = {"source_person": obj, "destination_person": self.destination}
        return super().get_form_kwargs()

    def get_queryset(self):
        qs = (
            Person.objects.filter(merged_into__isnull=True)
            .prefetch_related("hosted_episodes", "guest_appearances")
            .select_related("merged_into")
        )
        destination_id = self.kwargs.get("destination_id")
        try:
            self.destination = qs.get(id=destination_id)
        except ObjectDoesNotExist as odne:
            raise Http404 from odne
        return qs

    def get_object(self, queryset=None):
        self.object = super().get_object(queryset=queryset)  # type: ignore
        return self.object

    def get_context_data(self, **kwargs):
        if not hasattr(self, "object"):
            self.get_object()
        context = super().get_context_data(**kwargs)
        context["destination"] = self.destination
        context["conflict_data"] = self.object.get_potential_merge_conflicts(
            self.destination
        )
        return context


class PodcastEpisodeDescendantMixin(SelectPrefetchRelatedMixin):
    """
    Allows the episode queryset to be filtered by the podcast it comes from.
    """

    podcast: Podcast | None = None
    if TYPE_CHECKING:
        queryset: QuerySet[Episode] | None

    def get_queryset(self):
        podcast_id = self.kwargs.get("podcast_id", None)  # type: ignore
        if not podcast_id:  # no cov
            raise Http404
        try:
            self.podcast = Podcast.objects.get(pk=podcast_id)
        except ObjectDoesNotExist as ode:  # no cov
            raise Http404 from ode
        self.queryset = Episode.objects.filter(podcast=self.podcast)
        return super().get_queryset()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)  # type: ignore
        context["podcast"] = self.podcast
        return context


class EpisodeListView(LoginRequiredMixin, PodcastEpisodeDescendantMixin, ListView):
    """View all episodes for given podcast"""

    model = Episode
    pk_url_kwarg = "id"
    context_object_name = "episodes"
    paginate_by = 50
    ordering = ["-release_datetime", "-ep_num"]
    select_related = ["podcast", "season"]


class EpisodeDetailView(LoginRequiredMixin, PodcastEpisodeDescendantMixin, DetailView):
    """View a given episode's details."""

    model = Episode
    pk_url_kwarg = "id"
    context_object_name = "episode"
    select_related = ["podcast", "season"]
    prefetch_related = [
        "analysis_group",
        "hosts_detected_from_feed",
        "guests_detected_from_feed",
    ]


class EpisodeUpdateView(LoginRequiredMixin, PodcastEpisodeDescendantMixin, UpdateView):
    """Edit a given episode's details."""

    model = Episode
    pk_url_kwarg = "id"
    context_object_name = "episode"
    fields = [
        "title",
        "ep_num",
        "ep_type",
        "analysis_group",
        "hosts_detected_from_feed",
        "guests_detected_from_feed",
    ]

    def get_success_url(self):
        if messaging_enabled():
            messages.success(self.request, _("Episode updated"))
        return super().get_success_url()

    def form_invalid(self, form):  # no cov
        if messaging_enabled():
            messages.error(
                self.request, _("Episode could not be updated. See errors below.")
            )
        return super().form_invalid(form)


class EpisodeDeleteView(LoginRequiredMixin, PodcastEpisodeDescendantMixin, DeleteView):
    """Delete a given episode."""

    model = Episode
    pk_url_kwarg = "id"
    context_object_name = "episode"
    object: Episode
    select_related = ["podcast", "season"]
    prefetch_related = [
        "analysis_group",
        "hosts_detected_from_feed",
        "guests_detected_from_feed",
    ]
    podcast: Podcast

    def get_success_url(self):
        if messaging_enabled():
            messages.success(self.request, _("Episode deleted"))
        return reverse_lazy(
            "podcast_analyzer:episode-list", kwargs={"podcast_id": self.podcast.pk}
        )


class AnalysisGroupListView(LoginRequiredMixin, SelectPrefetchRelatedMixin, ListView):
    """List of all analysis groups."""

    model = AnalysisGroup
    context_object_name = "groups"
    paginate_by = 25
    prefetch_related = ["podcasts", "seasons", "episodes"]
    ordering = ["name", "-created"]


class AnalysisGroupDetailView(
    LoginRequiredMixin, SelectPrefetchRelatedMixin, DetailView
):
    """Details for a given analysis group."""

    model = AnalysisGroup
    pk_url_kwarg = "id"
    context_object_name = "group"
    prefetch_related = ["podcasts", "seasons", "episodes"]


class AnalysisGroupUpdateView(
    LoginRequiredMixin, SelectPrefetchRelatedMixin, UpdateView
):
    """Update a given analysis group."""

    model = AnalysisGroup
    pk_url_kwarg = "id"
    context_object_name = "group"
    form_class = AnalysisGroupForm
    prefetch_related = ["podcasts", "seasons", "episodes"]
    object: AnalysisGroup

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["initial"]["podcasts"] = self.object.podcasts.all()
        kwargs["initial"]["seasons"] = self.object.seasons.all()
        kwargs["initial"]["episodes"] = self.object.episodes.all()
        return kwargs

    def form_valid(self, form):
        self.object = form.save()
        self.object.podcasts.set(form.cleaned_data["podcasts"])
        self.object.seasons.set(form.cleaned_data["seasons"])
        self.object.episodes.set(form.cleaned_data["episodes"])
        if messaging_enabled():
            messages.success(self.request, _("Analysis group updated"))
        return HttpResponseRedirect(self.get_success_url())


class AnalysisGroupCreateView(LoginRequiredMixin, CreateView):
    """Create a new analysis group."""

    model = AnalysisGroup
    form_class = AnalysisGroupForm
    object: AnalysisGroup

    def form_valid(self, form):
        self.object = AnalysisGroup.objects.create(name=form.cleaned_data["name"])
        logger.debug(
            f"Created new analysis group with name: {form.cleaned_data['name']}"
        )
        logger.debug(
            f"Adding {len(form.cleaned_data['podcasts'])} podcasts, "
            f"{len(form.cleaned_data['seasons'])} seasons and "
            f"{len(form.cleaned_data['episodes'])} episodes."
        )
        self.object.podcasts.set(form.cleaned_data["podcasts"])
        self.object.seasons.set(form.cleaned_data["seasons"])
        self.object.episodes.set(form.cleaned_data["episodes"])
        if messaging_enabled():
            messages.success(self.request, _("Analysis group created"))
        return HttpResponseRedirect(self.object.get_absolute_url())


class AnalysisGroupDeleteView(
    LoginRequiredMixin, SelectPrefetchRelatedMixin, DeleteView
):
    """Delete a given analysis group."""

    model = AnalysisGroup
    pk_url_kwarg = "id"
    context_object_name = "group"
    object: AnalysisGroup
    prefetch_related = ["podcasts", "seasons", "episodes"]

    def get_success_url(self):
        if messaging_enabled():
            messages.success(self.request, _("Analysis group deleted"))
        return reverse_lazy("podcast_analyzer:ag-list")


class TagPodcastListView(LoginRequiredMixin, SelectPrefetchRelatedMixin, ListView):
    """
    List the podcasts for the given tag.
    """

    model = Podcast
    slug_field = "tag_slug"
    context_object_name = "podcasts"
    paginate_by = 25
    prefetch_related = ["episodes", "seasons", "itunes_categories", "tags"]
    ordering = ["title", "-created"]
    tag: Podcast.tags.tag_model  # type: ignore

    def get_queryset(self):
        try:
            self.tag = Podcast.tags.tag_model.objects.get(
                slug=self.kwargs.get("tag_slug", None)
            )
        except ObjectDoesNotExist as odne:
            raise Http404 from odne
        self.queryset = Podcast.objects.filter(tags__in=[self.tag])
        return super().get_queryset()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tag"] = self.tag
        return context
