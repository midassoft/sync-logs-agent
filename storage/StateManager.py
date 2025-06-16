# -*- coding: utf-8 -*-

from __future__ import print_function, division, absolute_import, unicode_literals
class StateManager:
    def __init__(self, storage):
        self.storage = storage
        self.state = {
            'last_position': 0,
            'pending_batches': []
        }
        self._load()

    def _load(self):
        """
        Load the state from the storage.

        This method is called when the class is instanced.
        """
        saved_state = self.storage.load()
        if saved_state:
            self.state = saved_state

    def save(self):
        """
        Save the current state to the storage.

        This method persists the current state by using the storage's
        save method. It is called whenever the state is updated.
        """

        self.storage.save(self.state)

    def update_position(self, position):
        """
        Update the last known position.

        This method updates the 'last_position' key in the state with the
        provided position and persists the updated state using the storage's
        save method.

        :param position: The new position to be updated.
        :type position: int
        """

        self.state['last_position'] = position
        self.save()

    def add_pending_batch(self, batch):
        """
        Add a pending batch to the state.

        This method adds the provided batch to the 'pending_batches' key in the
        state and persists the updated state using the storage's save method.

        :param batch: The batch to be added.
        :type batch: dict
        """
        self.state['pending_batches'].append(batch)
        self.save()

    def increment_batch_retry(self, batch_id):
        """
        Incrementa el contador de reintentos para un batch específico y guarda el estado.
        Devuelve el nuevo contador de reintentos, o -1 si el batch no se encuentra.
        """
        for batch_in_state in self.state.get('pending_batches', []):
            if batch_in_state.get('id') == batch_id:
                batch_in_state['retry_count'] = batch_in_state.get('retry_count', 0) + 1
                self.save()
                return batch_in_state['retry_count']
        return -1

    def remove_pending_batch(self, batch_id):
        self.state['pending_batches'] = [
            b for b in self.state['pending_batches'] if b['id'] != batch_id
        ]
        self.save()